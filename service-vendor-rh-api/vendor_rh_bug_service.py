# !/usr/bin/env python
"""
created 2021-09-20
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import os
import signal
import sys
import traceback

import boto3
from requests.packages import urllib3
from sqlalchemy.exc import OperationalError
from vendor_rh_api_client import RedHatApiClient
from vendor_rh_exceptions import VendorDisabled, ServiceNotConfigured, VendorExceptions, LambdaTimeOutException
from vendor_rh_supported_products import supported_products

from db_client import Database

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
urllib3.disable_warnings()


def initiate(*_args, **_kwargs):
    """
       Vendor Bug Service
       # keeps the managedProduct versions in sync with existing SN CIs
       1. query sn for supported vendor products and retrieve software versions
       2a. add a managedProduct if not exist
       2b. skip existing managedProducts based on lastExecution timestamp
       2c. update existing managedProduct with current software versions
       3. generate bugzilla search url for managedProduct filters
       4. search bugs
       4. insert bug updates
       5. update lastExecution timestamp
       6a. update services/serviceExecution tables
       6b. send error to sn eventManagement
    :return:
    """
    # print the event message
    logger.info(f"received event message - {_args[0]}")

    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    # service configuration
    vendor_id = "rh"
    service_id = "rh-bug-svc"
    service_name = "Red Hat Bug Service"
    service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    rh_api_client = RedHatApiClient(vendor_id=vendor_id)

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')
    new_bugs_updates = False


# last executed gap is used to skip managed products processed in the last 6 hours
    utc_now = datetime.datetime.utcnow()
    last_executed_gap = utc_now - datetime.timedelta(hours=6)
    counter = {
        "updated_bugs": 0,
        "skipped_bugs": 0,
        "inserted_bugs": 0,
        "sn_cmdb_cis_found": 0,
        "managed_products": 0,
        "new_managed_products": 0,
        "removed_managed_products": 0
    }
    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"

    # -----------------------------------------------------------------------------------------------------------------#
    #                                               AURORA DB CONFIG                                                   #
    # -----------------------------------------------------------------------------------------------------------------#
    managed_products_table = os.environ["MANAGED_PRODUCTS_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]
    bugs_table = os.environ["BUGS_TABLE"]

    # create a db session
    db_client = ""
    try:
        db_client = Database(
            db_host=os.environ["DB_HOST"],
            db_port=os.environ["DB_PORT"],
            db_user=os.environ["DB_USER"],
            db_password=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"]
        )
        db_client.create_session()

        rh_config = db_client.get_vendor_config(vendor_id=vendor_id, settings_table=settings_table)
        if not rh_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        rh_vendor_status = db_client.get_vendor_status(vendor_id=vendor_id, vendors_table=vendors_table)
        if not rh_vendor_status:
            message = f"{vendor_id} vendor services are disabled"
            logger.error(message)
            raise VendorDisabled(event_message=message, internal_message=message, vendor_id=vendor_id)

        # get service now settings for queries
        service_now_settings = db_client.get_vendor_config(vendor_id=service_now_id, settings_table=settings_table)
        if not service_now_settings:  # pragma: no cover - tested above
            message = f"ServiceNow connection info is missing - please check ServiceNow configurations page"
            internal_message = f"{service_now_id} does not exist in '{settings_table}' - can't start sync service"
            logger.error(internal_message)
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=service_now_id
            )

        sn_api_url = service_now_settings.value.get("snApiUrl")
        sn_secret_id = service_now_settings.value.get("secretId")

        if not sn_api_url or not sn_secret_id:
            internal_message = f"'{service_now_id}' config missing snApiUrl/secretId in '{settings_table}' - " \
                               f"can't start sync"
            logger.error(internal_message)
            message = f"ServiceNow connection info is missing - please check ServiceNow configurations page"
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=service_now_id
            )

        sn_auth_credentials = rh_api_client.get_aws_secret_value(sn_secret_id)
        sn_auth_token = base64.b64encode(
            f"{sn_auth_credentials['user']}:{sn_auth_credentials['pass']}".encode('ascii')
        ).decode('ascii')

        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS SYNC PROCESS                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
        sn_ci_query_base = rh_config.value.get('snAffectedCIQuery', "")

        # get managedProducts entries
        managed_products = db_client.get_managed_products(
            vendor_id=vendor_id, managed_products_table=managed_products_table)
        vendor_products = supported_products

        # stores managedProduct IDs for managedProducts with active CIs in SN CMDB
        active_managed_product_ids = []

        # global search variables
        rh_config = rh_config.value
        last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=int(rh_config['daysBack']) + 2)
        vendor_priorities = rh_config['vendorPriorities']
        vendor_statuses = rh_config['vendorStatuses']
        vendor_resolutions = rh_config['vendorResolutions']
        for product in vendor_products:
            product = rh_api_client.sn_sync(
                sn_api_url=sn_api_url, sn_auth_token=sn_auth_token, query_product=product,
                sn_ci_query_base=sn_ci_query_base
            )
            if not product.get("sn_ci_versions"):
                continue

            managed_product = [x for x in managed_products if product["value"] == x.name]
            if managed_product:
                managed_product = managed_product[0]
                active_managed_product_ids.append(managed_product.id)
                counter["managed_products"] += 1
                if managed_product.isDisabled:
                    logger.info(f"'{managed_product.name}' - skipping disabled product")
                    continue
                if managed_product.lastExecution:
                    if managed_product.lastExecution > last_executed_gap:
                        delta = utc_now - managed_product.lastExecution
                        delta_hours = '{:2.2f}'.format(delta.seconds / 3600)
                        logger.info(
                            f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                        )
                        continue
                    last_execution = managed_product.lastExecution - datetime.timedelta(days=2)
                vendor_priorities = managed_product.vendorPriorities
                vendor_statuses = managed_product.vendorStatuses
                vendor_resolutions = managed_product.vendorData["vendorResolutions"]

            else:
                managed_product = db_client.create_managed_product(
                    name=product["value"], vendor_id=vendor_id, vendor_priorities=vendor_priorities,
                    vendor_resolutions=vendor_resolutions, vendor_statuses=vendor_statuses,
                    versions=product["sn_ci_versions"], managed_products_table=managed_products_table
                )
                counter["new_managed_products"] += 1
                active_managed_product_ids.append(managed_product.id)

            # ensure that minor versions are converted to major versions
            # 3.3.4 ==> 3.3
            product["sn_ci_versions"] = [x[:3] for x in product["sn_ci_versions"]]
            counter["sn_cmdb_cis_found"] += 1

            # update managedProduct versions
            db_client.update_managed_product_versions(
                managed_product=managed_product, versions=product["sn_ci_versions"],
            )

        # ------------------------------------------------------------------------------------------------------------ #
        #                                              BUG SERVICE                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
            search_url = rh_api_client.generate_api_search_url(
                start_date=last_execution.strftime("%Y-%m-%d"),
                end_date=datetime.datetime.utcnow().strftime("%Y-%m-%d"), name=product["value"],
                vendor_priorities=vendor_priorities, vendor_statuses=vendor_statuses,
                vendor_resolutions=vendor_resolutions, versions=product["sn_ci_versions"]
            )
            product_bugs = rh_api_client.get_bugs(search_url=search_url, product_name=product["value"])
            if product_bugs:
                formatted_bugs = rh_api_client.format_bug_entry(
                    managed_product=managed_product, bugs=product_bugs,
                    sn_ci_filter=product['sysparm_query'], service_now_ci_table=product["service_now_ci_table"],
                    sn_ci_query_base=sn_ci_query_base
                )

                # get bug description with a multi-processing manager
                formatted_bugs = rh_api_client.bug_description_multi_processing(bugs=formatted_bugs)
                inserts = db_client.insert_bug_updates(bugs=formatted_bugs, bugs_table=bugs_table)
                if inserts['updated_bugs'] or inserts['inserted_bugs']:
                    new_bugs_updates = True
                counter["updated_bugs"] += inserts["updated_bugs"]
                counter["inserted_bugs"] += inserts["inserted_bugs"]
                logger.info(f"'{managed_product.name}' - sync completed | {json.dumps(inserts)}")  # pragma: no cover
            else:
                logger.info(f"'{managed_product.name}' - sync completed | 0 bugs updates")  # pragma: no cover

            setattr(managed_product, 'lastExecution', datetime.datetime.utcnow())
            db_client.conn.commit()

        # remove managedProduct and linked bugs that don't have an active CMDB CI
        removed_managed_products = db_client.remove_non_active_managed_products(
            bugs_table=bugs_table, managed_products_table=managed_products_table,
            active_managed_product_ids=active_managed_product_ids, vendor_id=vendor_id
        )

        counter['removed_managed_products'] += removed_managed_products
        logger.info(f"'{vendor_id}' sync completed - {json.dumps(counter)}")

        # on existing bug updates - trigger the bugEventProcessor
        if new_bugs_updates:
            logger.info(
                f"'{vendor_id}' - bug updates found | sending a trigger message to "
                f"{os.environ['BUG_EVENT_PROCESSOR_SERVICE_NAME']}"
            )
            message = json.dumps({'default': f"{vendor_id} bug updates found"})
            sns_client.publish(
                TopicArn=os.environ["SERVICE_SNS_TOPIC_ARN"], Subject="trigger", MessageStructure="json",
                Message=message, MessageAttributes={
                    "service": {"DataType": "String", "StringValue": os.environ['BUG_EVENT_PROCESSOR_SERVICE_NAME']}
                }
            )

        # update execution message
        if counter["sn_cmdb_cis_found"]:
            message = f"{counter['inserted_bugs']} new bugs published"
        elif not counter["managed_products"]:
            message = 'no active SN CIs matching enabled managed products were found'
        else:
            message = f"0 new bugs published"

        execution_service_message = message

    except (
            Exception, VendorExceptions
    ) as e:
        (exception_type, _exception_object, exception_traceback) = sys.exc_info()
        if isinstance(e, OperationalError):
            error_type = "Operational"
            execution_service_message = "Database connection error - we are working on getting this fixed as soon as " \
                                        "possible"
            severity = 1
        elif isinstance(e, LambdaTimeOutException):
            error_type = "Program"
            severity = 1

        elif isinstance(e, VendorExceptions):
            error_type = "Operational"
            execution_service_message = e.event_message
            severity = 1
        else:
            error_type = "Program"
            severity = 1

        # vendorDisabled exceptions are not considered service error events
        if not isinstance(e, (VendorDisabled, ServiceNotConfigured)):
            # generate an sn event record and send to the sns topic
            service_status = "ERROR"
            service_error = 1
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type=error_type, severity=severity,
                additional_info=additional_info,
                logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )
        else:
            service_status = "NOT CONFIGURED"
            service_error = 1
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        error_message = {
            "errorType": str(exception_type),
            "errorMsg": str(e),
            "source": "",
            "service": f"{str(filename)} - line {line_number}",
        }
        logger.error(json.dumps(error_message, default=str))
        message = error_message

    rh_api_client.bug_zero_vendor_status_update(
        service_status=service_status,
        db_client=db_client,
        vendor_id=vendor_id,
        service_execution_table=service_execution_table,
        services_table=services_table,
        service_id=service_id,
        started_at=started_timestamp,
        message=execution_service_message,
        service_name=service_name,
        error=service_error
    )

    return {
        "message": message
    }


def timeout_handler(_signal, _frame):
    """
    Handle SIGALRM exception when lambda timeout is about to be reached
    :param _signal:
    :param _frame:
    :return:
    """
    raise LambdaTimeOutException


if __name__ == "__main__":  # pragma: no cover
    # when testing, enable stdout logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "rh-bug-svc",
            "log_group_name": "rh-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )

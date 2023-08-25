# !/usr/bin/env python
"""
   created 2021-11-02
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
from vendor_veeam_api_client import VeeamApiClient

from db_client import Database
from vendor_exceptions import VendorDisabled, ServiceNotConfigured, VendorExceptions, SnCiFieldMissing, \
    LambdaTimeOutException

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
       3. search for kb articles
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
    vendor_id = "veeam"
    service_id = "veeam-bug-svc"
    service_name = "Veeam Bug Service"
    service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    veeam_api_client = VeeamApiClient(vendor_id=vendor_id)

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
        "sn_packages_found": 0,
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

        veeam_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not veeam_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        veeam_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not veeam_vendor_settings:
            message = f"{vendor_id} vendor services are disabled"
            logger.error(message)
            raise VendorDisabled(event_message=message, internal_message=message, vendor_id=vendor_id)

        # get service now settings for queries
        service_now_settings = db_client.get_service_config(vendor_id=service_now_id, settings_table=settings_table)
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

        sn_auth_credentials = veeam_api_client.get_aws_secret_value(sn_secret_id)
        sn_auth_token = base64.b64encode(
            f"{sn_auth_credentials['user']}:{sn_auth_credentials['pass']}".encode('ascii')
        ).decode('ascii')

        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS SYNC PROCESS                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
        sn_ci_query_base = veeam_config.value.get('snAffectedCIQuery', "")

        vendor_products = veeam_api_client.crawl_vendor_products()
        # stores managedProduct IDs for managedProducts with active CIs in SN CMDB
        active_managed_product_ids = []
        # reset the versions for each managed_product
        for product in vendor_products:
            # get managedProducts entries
            product_versions = set()
            product_major_versions = set()
            managed_product = db_client.get_managed_products(
                vendor_id=vendor_id, managed_products_table=managed_products_table,
                product_name=product['name']
            )
            # get all sn instances discovered for a given product
            active_cis = veeam_api_client.sn_sync(
                sn_api_url=sn_api_url, sn_auth_token=sn_auth_token, query_product=product,
                sn_ci_query_base=sn_ci_query_base
            )
            if not active_cis:
                continue
            for ci in active_cis:
                counter["sn_packages_found"] += 1
                product_version = ci.get("version", None)
                if not product_version:
                    raise SnCiFieldMissing(
                        url=ci["sn_query_url"],
                        internal_message=f"SN CI missing/empty required field - 'version' | SN CI sys_id: "
                                         f"'{ci['sys_id']}",
                        event_message=f"SN CI os version missing - we are actively working on a fix",
                        field_name='version',
                        ci_sys_id=ci['sys_id']
                    )
                product_major_version = product_version.split(".")[0]
                product_versions.add(product_version)
                product_major_versions.add(product_major_version)

            # set the global earliest date to get bugs ( used if a managed products is missing a lastExecution field )
            bugs_days_back = int(veeam_config.value["daysBack"])

            if managed_product:
                counter["managed_products"] += 1
                managed_product = managed_product[0]
                active_managed_product_ids.append(managed_product.id)
                if managed_product.isDisabled:
                    logger.info(f"'{managed_product.name}' - skipping disabled product")
                    continue

                if managed_product.lastExecution and managed_product.lastExecution > last_executed_gap:
                    delta = utc_now - managed_product.lastExecution
                    delta_hours = '{:2.2f}'.format(delta.seconds / 3600)
                    logger.info(
                        f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                    )
                    continue
                if managed_product.lastExecution:
                    bugs_days_back = (datetime.datetime.utcnow() - managed_product.lastExecution).days

                db_client.update_managed_product_versions(
                    managed_product=managed_product, versions=product_versions,
                    major_versions=product_major_versions
                )
            else:
                managed_product = db_client.create_managed_product(
                    name=product['name'], vendor_id=vendor_id, versions=list(product_versions),
                    major_versions=product_major_versions, vendor_product_id=product['abbr'],
                    managed_products_table=managed_products_table, service_settings=veeam_config.value
                )
                counter["new_managed_products"] += 1
                active_managed_product_ids.append(managed_product.id)

        # ------------------------------------------------------------------------------------------------------------ #
        #                                              BUG SERVICE                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
            # get all the kb articles for a given product
            product_kb_entries = veeam_api_client.get_kb_article_links(product=product)
            logger.info(
                f"'{product['name']}' - {len(product_kb_entries)} KB entries retrieved | creating a crawl queue"
            )
            # download and parse kb html pages and format bug entries
            product_bugs = veeam_api_client.get_bugs(
                bugs_days_back=bugs_days_back, kb_entries=product_kb_entries, managed_product=managed_product,
                sn_ci_query_base=sn_ci_query_base
            )
            if product_bugs:
                inserts = db_client.insert_bug_updates(
                    bugs=product_bugs, bugs_table=bugs_table, product_name=managed_product.name
                )
                if inserts['updated_bugs'] or inserts['inserted_bugs']:
                    new_bugs_updates = True
                counter["updated_bugs"] += inserts["updated_bugs"]
                counter["inserted_bugs"] += inserts["inserted_bugs"]
                counter["skipped_bugs"] += inserts["skipped_bugs"]
                logger.info(
                    f"'{managed_product.name}' - sync completed | {json.dumps(inserts)}"
                )
            else:
                logger.info(f"'{managed_product.name}' - sync completed | 0 new bugs found")
                db_client.conn.commit()

            logger.info(f"'{managed_product.name}' - updating lastExecution")
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
        if counter["sn_packages_found"]:
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
        if isinstance(e, LambdaTimeOutException):
            error_type = "Program"
            severity = 1

        elif isinstance(e, OperationalError):
            error_type = "Operational"
            execution_service_message = "Database connection error - we are working on getting this fixed as soon as " \
                                        "possible"
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

    veeam_api_client.bug_zero_vendor_status_update(
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
            "function_name": "veeam-bug-svc",
            "log_group_name": "veeam-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )

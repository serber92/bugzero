# !/usr/bin/env python
"""
created 2021-07-13
"""
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
from vendor_msft365_api_client import Msft365ApiClient

from db_client import Database
from vendor_exceptions import VendorDisabled, ServiceNotConfigured, VendorExceptions, LambdaTimeOutException

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
    1. retrieve enabled managedProducts
    1. get all vendorProducts and vendorProductVersions
    2. query SN for CI matching the vendorProductVersions
    3a. append new productVersions to mangedProducts.vendorData.vendorProductVersion>ids
    3b. remove managedProduct that no longer have correlating SN CI(S)
    4. retrieve and insert bugs for relevant managedProducts
    :return:
    """
    # use a signal handler to set an alarm that will invoke timeout_handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    vendor_id = "msft365"
    service_id = "msft365-bug-svc"
    service_name = "MSFT 365 Bug Service"
    # service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    msft_365_api_client = Msft365ApiClient(vendor_id=vendor_id)
    counter = {
        "updated_bugs": 0,
        "inserted_bugs": 0,
        "skipped_bugs": 0,
        "managed_products": 0,
        "new_managed_products": 0,
        "removed_managed_products": 0
    }

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')
    new_bugs_updates = False

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
    bugs_table = os.environ["BUGS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]

    utc_now = datetime.datetime.utcnow()
    last_executed_gap = utc_now - datetime.timedelta(hours=6)

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

        # ------------------------------------------------------------------------------------------------------------ #
        #                                               GLOBAL SETTINGS                                                #
        # ------------------------------------------------------------------------------------------------------------ #

        msft_365_config = db_client.get_settings(vendor_id=vendor_id, settings_table=settings_table)
        if not msft_365_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        msft_365_vendor = db_client.get_vendor(vendor_id=vendor_id, vendors_table=vendors_table)
        if not msft_365_vendor:
            message = f"{vendor_id} vendor services are disabled"
            logger.error(message)
            raise VendorDisabled(event_message=message, internal_message=message, vendor_id=vendor_id)

        admin_credentials = msft_365_api_client.get_aws_secret_value(secret_name=msft_365_config.value.get("secretId"))
        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS SYNC PROCESS                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        global_days_back = int(msft_365_config.value["daysBack"])
        global_last_execution = utc_now - datetime.timedelta(days=global_days_back)

        # get managedProducts entries
        managed_products = db_client.get_managed_products(
            vendor_id=vendor_id, managed_products_table=managed_products_table)

        last_execution_range = [
            x.lastExecution if x.lastExecution else global_last_execution for x in managed_products
        ]
        last_execution_range.append(global_last_execution)
        last_execution = max(last_execution_range)
        bug_days_back = (utc_now - last_execution).days

        # generate msft admin dashboard access tokens
        access_tokens = msft_365_api_client.gen_admin_dashboard_tokens(
            username=admin_credentials['username'], password=admin_credentials['password'])

        # get all service issues
        msft_365_services = msft_365_api_client.get_service_issues(days_back=bug_days_back, tokens=access_tokens)
        msft_365_services = sorted(msft_365_services, key=lambda x: x['Name'])

        # stores managedProduct IDs for managedProducts with active CIs in SN CMDB
        active_managed_product_ids = []

        for product in msft_365_services:
            logger.info(f"'{product['Name']}' - syncing cloud service")

            # search for an existing managedProducts
            managed_product = [x for x in managed_products if product['Name'] == x.name]
            if not managed_product:
                counter["new_managed_products"] += 1

                # create a new managedProduct
                managed_product = db_client.create_managed_product(
                    name=product['Name'], vendor_id=vendor_id, managed_products_table=managed_products_table,
                    service_settings=msft_365_config.value, versions=[]
                )
                # store the managedProduct ID to skip it's removal
                active_managed_product_ids.append(managed_product.id)
            else:
                counter["managed_products"] += 1
                managed_product = managed_product[0]
                # store the managedProduct ID to skip it's removal
                active_managed_product_ids.append(managed_product.id)

            # skip disabled managedProducts
            if managed_product.isDisabled:
                logger.info(f"'{managed_product.name}' - skipping disabled product")
                continue

            # skip recently processed managedProducts
            if managed_product.lastExecution and managed_product.lastExecution > last_executed_gap:
                delta = utc_now - managed_product.lastExecution
                delta_hours = '{:2.2f}'.format(delta.seconds / 3600)
                logger.info(
                    f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                )
                continue

    # -----------------------------------------------------------------------------------------------------------------#
    #                                                   BUG SERVICE                                                    #
    # -----------------------------------------------------------------------------------------------------------------#
            # set bugs_days_back based on managedProduct or use global_days_back
            if managed_product.lastExecution:
                bugs_days_back = (datetime.datetime.utcnow() - managed_product.lastExecution).days
            else:
                bugs_days_back = global_days_back

            managed_product_last_execution = utc_now - datetime.timedelta(days=bugs_days_back)
            # run the bug retrieval process
            service_bugs = msft_365_api_client.filter_service_health_issues(
                managed_product=managed_product, last_execution=managed_product_last_execution,
                service_issue=product['MessagesByClassification']
            )

            if service_bugs:
                inserts = db_client.insert_bug_updates(
                    bugs=service_bugs, bugs_table=bugs_table, product_name=managed_product.name
                )
                if inserts["updated_bugs"] or inserts["inserted_bugs"]:
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

            # update the lastExecution field
            managed_product.lastExecution = utc_now
            db_client.conn.commit()

        # remove managedProduct and linked bugs that don't have an active CMDB CI
        removed_managed_products = db_client.remove_non_active_managed_products(
            bugs_table=bugs_table, managed_products_table=managed_products_table,
            active_managed_product_ids=active_managed_product_ids, vendor_id=vendor_id
        )
        counter['removed_managed_products'] += removed_managed_products
        logger.info(f"'{vendor_id}' - sync completed | {json.dumps(counter)}")

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
        if counter["managed_products"] or counter["new_managed_products"]:
            message = f"{counter['inserted_bugs']} new bugs published"
        elif not counter["managed_products"] and not counter["new_managed_products"]:
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
            execution_service_message = str(e)
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

    msft_365_api_client.bug_zero_vendor_status_update(
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
            "function_name": "msft365-bug-svc",
            "log_group_name": "msft365-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )

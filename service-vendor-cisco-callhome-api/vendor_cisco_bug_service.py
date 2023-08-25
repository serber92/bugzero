#!/usr/bin/env python3
"""
created 2021-04-27
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
from sqlalchemy.exc import OperationalError

from db_client import Database
from vendor_cisco_api_client import CiscoApiClient
from vendor_exceptions import LambdaTimeOutException, ServiceNotConfigured, VendorDisabled, VendorExceptions

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sql_logger = logging.getLogger('sqlalchemy.engine')
sql_logger.setLevel(logging.WARNING)


VENDOR_BUG_PRIORITY_MAP = {
    "1": "Catastrophic",
    "2": "Severe",
    "3": "Moderate",
    "4": "Minor",
    "5": "Cosmetic",
    "6": "Enhancement"
}

VENDOR_BUG_STATUS_MAP = {
    "O": "Open",
    "F": "Fixed",
    "T": "Terminated"
}


def initiate(*_args, **_kwargs):
    """
       1. get all active Cisco clients and set the earliest bug date to retrieve
       2. retrieve new bugs
       3. filter bugs based on earliest bug date
       4. iterate over clients with relevant managed-products families and insert bug to (env)-vendor-bugs-table

    :return:
    """
    # print the event message
    logger.info(f"received event message - {_args[0]}")

    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')

    vendor_id = "cisco"
    service_id = "cisco-bug-svc"
    service_name = "Cisco Bug Service"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    cisco_api_client = CiscoApiClient(
        vendor_id=vendor_id
    )
    # last executed gap is used to skip managed products processed in the last 6 hours
    utc_now = datetime.datetime.utcnow()
    last_executed_gap = utc_now - datetime.timedelta(hours=6)
    counter = {
        "updated_bugs": 0,
        "skipped_bugs": 0,
        "inserted_bugs": 0,
        "new_managed_products": 0,
        "managed_products": 0,
        "removed_managed_products": 0
    }
    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                 AURORA DB CONFIG                                                 #
    # ---------------------------------------------------------------------------------------------------------------- #
    logger.info(f"environment variables retrieved - {os.environ}")

    managed_products_table = os.environ["MANAGED_PRODUCTS_TABLE"]
    bugs_table = os.environ["BUGS_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]
    new_bugs_updates = False

    db_client = ""
    try:
        db_client = Database(
            db_host=os.environ["DB_HOST"],
            db_port=os.environ["DB_PORT"],
            db_user=os.environ["DB_USER"],
            db_password=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"],
        )
        db_client.create_session()

        cisco_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not cisco_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        cisco_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not cisco_vendor_settings:
            message = f"{vendor_id} vendor services are disabled"
            logger.error(message)
            raise VendorDisabled(event_message=message, internal_message=message, vendor_id=vendor_id)

        # ------------------------------------------------------------------------------------------------------------ #
        #                                         CISCO AUTHENTICATION FLOW                                            #
        # ------------------------------------------------------------------------------------------------------------ #
        # get the cisco service client_id and secret from AWS secrets manager
        cisco_config = cisco_config.value
        if "serviceSecretId" not in cisco_config or not cisco_config["serviceSecretId"]:
            internal_message = "serviceSecretId is missing or empty - cant start authentication flow - the tenant " \
                               "has not configured cisco call home"
            logger.error(
                internal_message
            )
            raise ServiceNotConfigured(
                event_message=f"'{vendor_id}' - login credentials are not configured | see vendor configuration page",
                internal_message=internal_message,
                service_id=service_id
            )

        # get the cisco support client_id and secret from AWS secrets manager
        if "supportSecretId" not in cisco_config or not cisco_config["supportSecretId"]:
            internal_message = "supportSecretId is missing or empty - cant start authentication flow - the tenant " \
                               "has not configured cisco call home"
            logger.error(internal_message)
            raise ServiceNotConfigured(
                event_message=f"'{vendor_id}' - login credentials are not configured | see vendor configuration page",
                internal_message=internal_message,
                service_id=service_id
            )

        service_secret_id = cisco_config.get("serviceSecretId", None)
        support_secret_id = cisco_config.get("supportSecretId", None)
        if not service_secret_id or not support_secret_id:
            internal_message = f"'{vendor_id}' - '{settings_table}' config missing " \
                               f"serviceSecretId/supportSecretId | cant start service"
            logger.error(internal_message)
            message = f"'{vendor_id}' - vendor credentials info is missing | please check vendor configurations " \
                      f"page"
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=vendor_id
            )

        cisco_customer_id, support_token, service_token = cisco_api_client.cisco_authentication(
            cisco_config=cisco_config
        )

        # ------------------------------------------------------------------------------------------------------------ #
        #                                              SYNC PROCESS                                                    #
        # ------------------------------------------------------------------------------------------------------------ #
        # allowed hardware product types to be inserted as managed products
        allowed_product_types = [
            "Data Center Switches",
            "Routers",
            "Security",
            "Switches",
            "Unified Communications",
            "Wireless",
        ]
        # get hardware inventory from the service API
        logger.info(f"'{vendor_id}' - getting inventory from Service API")
        hardware_inventory = cisco_api_client.get_hardware_inventory(
            cisco_customer_id=cisco_customer_id["customerId"],
            cisco_service_token=service_token,
        )

        # stores managedProduct IDs for managedProducts with active products in vmware skyline
        active_managed_product_ids = []
        # dedup productFamily
        dedup = set()
        for p in hardware_inventory:
            # skipping not supported products
            if p["productType"] not in allowed_product_types:
                continue
            # skipping product for a productFamily that was already processed
            if p["productFamily"] in dedup:
                continue
            dedup.add(p["productFamily"])

            managed_product = db_client.get_managed_product(
                vendor_id=vendor_id, managed_products_table=managed_products_table, product_name=p["productFamily"]
            )
            # set the global earliest date to get bugs ( used if a managed products is missing a lastExecution field )
            bugs_days_back = int(cisco_config["daysBack"])
            if managed_product:
                active_managed_product_ids.append(managed_product[0].id)
                counter["managed_products"] += 1
                managed_product = managed_product[0]
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
                    logger.info(f"'{managed_product.name}' - found existing managed Product")

            else:
                # create a new managedProduct
                managed_product = db_client.create_managed_product(
                    name=p["productFamily"], vendor_id=vendor_id, managed_products_table=managed_products_table,
                    service_settings=cisco_config
                )
                active_managed_product_ids.append(managed_product.id)
                counter["new_managed_products"] += 1

            earliest_bug_date = utc_now - datetime.timedelta(days=bugs_days_back)
            # create a list of all the inventory products matching the managed product
            child_products = []
            for h in hardware_inventory:
                if h["productFamily"] == managed_product.name:
                    child_products.append(h)
            if not child_products:
                continue

        # ------------------------------------------------------------------------------------------------------------ #
        #                                              BUG PROCESS                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
            # create a vendorPriorityValue: vendorPriorityLabel dictionary
            severities = {
                x["vendorPriority"]:  VENDOR_BUG_PRIORITY_MAP[str(x["vendorPriority"])] for x in
                managed_product.vendorPriorities
            }
            statuses = {
                str(s):  VENDOR_BUG_STATUS_MAP[str(s)] for s in managed_product.vendorStatuses
            }

            prod_family_bugs = cisco_api_client.bugs_by_prod_family_and_sv(
                product_family_name=managed_product.name,
                products=child_products,
                cisco_service_token=support_token,
            )

            # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
            sn_ci_query_base = cisco_config.get('snAffectedCIQuery', "")

            filtered_bugs = cisco_api_client.filter_bugs(
                bugs=prod_family_bugs, vendor_severities=severities, vendor_statuses=statuses,
                managed_product_id=managed_product.id, products=child_products, earliest_bug_date=earliest_bug_date,
                sn_ci_query_base=sn_ci_query_base
            )

            if filtered_bugs:
                logger.info(
                    f"'{managed_product.name}' - {len(filtered_bugs)} bug updates found | inserting to '{bugs_table}'"
                )
                # insert bugs to bugs-table
                inserts = db_client.insert_bug_updates(bugs=filtered_bugs, bugs_table=bugs_table)
                if inserts["updated_bugs"] or inserts["inserted_bugs"]:
                    new_bugs_updates = True
                counter["updated_bugs"] += inserts["updated_bugs"]
                counter["skipped_bugs"] += inserts["skipped_bugs"]
                counter["inserted_bugs"] += inserts["inserted_bugs"]

                # update lastExecution timestamp
                logger.info(f"'{managed_product.name}' - updating lastExecution")
            setattr(managed_product, 'lastExecution', datetime.datetime.utcnow())
            db_client.conn.commit()

        # remove managedProduct that don't have active products in skyline
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
        if counter["managed_products"] or counter["new_managed_products"]:
            message = f"{counter['inserted_bugs']} new bugs published"
        elif not counter["managed_products"] and not counter["new_managed_products"]:
            message = f"currently there are no products to process"
        else:
            message = f"0 new bugs published"

        execution_service_message = message
        logger.info(message)
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

    cisco_api_client.bug_zero_vendor_status_update(
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
            "function_name": "cisco-bug-svc",
            "log_group_name": "cisco-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )

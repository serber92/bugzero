#!/usr/bin/env python3
"""
created 2021-09-19
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
from sqlalchemy.exc import OperationalError

from db_client import Database
from vendor_exceptions import VendorDisabled, ServiceNotConfigured, VendorExceptions, LambdaTimeOutException
from vendor_mongodb_api_client import MongoApiClient

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sql_logger = logging.getLogger('sqlalchemy.engine')
sql_logger.setLevel(logging.WARNING)


def initiate(*_args, **_kwargs):
    """
       1. get mongoDB managed products and set the earliest bug date to retrieve
       2. retrieve new bugs
       3. filter bugs based on earliest bug date
    :return:
    """
    # print the event message
    logger.info(f"received event message - {_args[0]}")

    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    vendor_id = "mongodb"
    service_id = "mongodb-bug-svc"
    service_name = "MongoDB Bug Service"
    service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    mongodb_api_client = MongoApiClient(
        vendor_id=vendor_id
    )

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

    # create a db session
    db_client = ""
    message = ""
    try:
        db_client = Database(
            db_host=os.environ["DB_HOST"],
            db_port=os.environ["DB_PORT"],
            db_user=os.environ["DB_USER"],
            db_password=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"],
        )
        db_client.create_session()

        mongodb_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not mongodb_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        mongodb_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not mongodb_vendor_settings:
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

        sn_auth_credentials = mongodb_api_client.get_aws_secret_value(sn_secret_id)
        sn_auth_token = base64.b64encode(
            f"{sn_auth_credentials['user']}:{sn_auth_credentials['pass']}".encode('ascii')
        ).decode('ascii')

        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS SYNC PROCESS                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
        sn_ci_query_base = mongodb_config.value.get('snAffectedCIQuery', "")
        # stores managedProduct IDs for managedProducts with active CIs in SN CMDB
        active_managed_product_ids = []
        # look for vendor instances in SN
        sn_versions = mongodb_api_client.sn_sync(
            sn_api_url=sn_api_url, sn_auth_token=sn_auth_token, sn_ci_query_base=sn_ci_query_base
        )
        # convert to seconds for API query
        last_execution_seconds = int(mongodb_config.value["daysBack"]) * 86400
        while True:
            if sn_versions:
                # mongodb can only have one managedProduct and should be created if not already exist
                managed_products = db_client.get_managed_products_by_vendor(
                    managed_products_table=managed_products_table, vendor_id=vendor_id
                )
                # while vendor_managed_products could only have 1 product, the response is still treated like a list for
                # feature support for more mongodb products
                # set default from bugsDaysBack
                if managed_products:
                    logger.info(f"'{vendor_id}' - found existing managedProduct")
                    counter["managed_products"] += 1
                    managed_product = managed_products[0]
                    active_managed_product_ids.append(managed_product.id)
                    if managed_product.isDisabled:
                        logger.info(f"'{managed_product.name}' - skipping disabled product")
                        break

                    if managed_product.lastExecution and managed_product.lastExecution > last_executed_gap:
                        execution_delta = utc_now - managed_product.lastExecution
                        delta_hours = '{:2.2f}'.format(execution_delta.seconds / 3600)
                        logger.info(
                            f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                        )
                        break

                    if managed_product.lastExecution:
                        last_execution_seconds = (
                                datetime.datetime.utcnow() - managed_product.lastExecution
                        ).seconds

                    db_client.update_managed_product_versions(managed_product=managed_product, versions=sn_versions)
                else:
                    managed_product = db_client.create_managed_product(
                        name="MongoDB Server", vendor_id=vendor_id, versions=sorted(list(sn_versions)),
                        managed_products_table=managed_products_table,
                        service_settings=mongodb_config
                    )
                    active_managed_product_ids.append(managed_product.id)
                    counter["new_managed_products"] += 1

                # gen filter map
                # calculate minutes since last execution for the JQL statement + 60 minutes for buffer
                minutes_since_last_execution = int(last_execution_seconds / 60 + 60)
                search_filter_map = mongodb_api_client.gen_search_filter_map(
                    managed_product=managed_product, minutes_since_last_execution=minutes_since_last_execution
                )

                # generate jql query for bug search
                jql_query = mongodb_api_client.create_jql_query(search_filter_map=search_filter_map)
                bugs_retrieved = mongodb_api_client.get_bugs(jql_statement=jql_query, product_name=managed_product.name)
                filtered_bugs = mongodb_api_client.format_bug_entry(
                    bugs=bugs_retrieved, managed_product_id=managed_product.id, sn_ci_query_base=sn_ci_query_base
                )
                process_counter = db_client.insert_bug_updates(
                    bugs_table=bugs_table, bugs=filtered_bugs, product_name=managed_product.name
                )

                # update product last execution
                if process_counter['inserted_bugs'] or process_counter['skipped_bugs']:
                    new_bugs_updates = True
                counter["inserted_bugs"] += process_counter['inserted_bugs']
                counter["skipped_bugs"] += process_counter['skipped_bugs']
                counter["updated_bugs"] += process_counter['updated_bugs']
                logger.info(f"'{managed_product.name}' - {json.dumps(process_counter, default=str)}")

                execution_service_message = f"'{managed_product.name}' - {counter['inserted_bugs']}' new bugs published"
                logger.info(f"'{managed_product.name}' - updating lastExecution")
                setattr(managed_product, 'lastExecution', datetime.datetime.utcnow())
                db_client.conn.commit()

                # update execution message
                if counter["inserted_bugs"] or counter["updated_bugs"]:
                    message = f"{counter['inserted_bugs'] + counter['updated_bugs']} new bugs updated"
                elif not counter["managed_products"] or not counter["new_managed_products"]:
                    message = 'no active SN CIs matching enabled managed products were found'
                else:
                    message = f"0 new bugs published"
                execution_service_message = message

            else:
                execution_service_message = f"'{vendor_id}' - no active SN CIs for vendor were found"
                message = execution_service_message
                logger.info(execution_service_message)
            break

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

    mongodb_api_client.bug_zero_vendor_status_update(
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
            "function_name": "mongodb-bug-svc",
            "log_group_name": "mongodb-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        })
    )

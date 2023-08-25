# !/usr/bin/env python
"""
created 2021-12-16
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

from db_client import Database
from vendor_aws_api_client import AwsApiClient
from vendor_aws_health_client import HealthClient
from vendor_aws_supported_products import supported_services
from vendor_exceptions import VendorDisabled, ServiceNotConfigured, VendorExceptions, \
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
       for each supported product:
       1. query AWS Resource Groups Tagging Api for enabled resources
          a. create a managed product if does not exist and resources were found
          b. skip recently processed and/or disabled managedProducts
          c. skip if API returns 0 resources and delete managedProduct if exist
       2. query Health API for health events
       3. insert bug updates
       4. update lastExecution timestamp
       5a. update services/serviceExecution tables
       5b. send error to sn eventManagement
    :return:
    """
    # print the event message
    logger.info(f"received event message - {_args[0]}")

    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    # service configuration
    vendor_id = "aws"
    service_id = "aws-bug-svc"
    service_name = "AWS Bug Service"
    service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    aws_api_client = AwsApiClient(vendor_id=vendor_id)

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

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')
    new_bugs_updates = False

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

        aws_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not aws_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        aws_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not aws_vendor_settings:
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

        sn_auth_credentials = aws_api_client.get_aws_secret_value(sn_secret_id)
        sn_auth_token = base64.b64encode(
            f"{sn_auth_credentials['user']}:{sn_auth_credentials['pass']}".encode('ascii')
        ).decode('ascii')
        if not sn_auth_token:
            pass

        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS SYNC PROCESS                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        role_arn = f"{aws_config.value.get('awsApiHealthApiRoleArn')}"
        assumed_role_object = aws_api_client.sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="AWSHealthCrossAccountSession"
        )
        cost_explorer_api = boto3.client(
            'ce',
            aws_access_key_id=assumed_role_object['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role_object['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role_object['Credentials']['SessionToken']
        )
        health_client = HealthClient(
            aws_access_key_id=assumed_role_object['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role_object['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role_object['Credentials']['SessionToken']
        )
        active_managed_product_ids = []
        aws_service_discovered = aws_api_client.get_service_usage_regions(
            cost_explorer_client=cost_explorer_api, supported_services=supported_services
        )

        for service in supported_services:
            # get managedProducts entries
            managed_product = db_client.get_managed_products(
                vendor_id=vendor_id, managed_products_table=managed_products_table,
                product_name=service['service_name']
            )

            if service['service_name'] in aws_service_discovered:
                active_regions = list(aws_service_discovered[service['service_name']].keys())
            elif service["bypass_inventory"]:
                active_regions = []
            else:
                continue

            active_regions.append('global')
            # set the global earliest date to get bugs ( used if a managed products is missing a lastExecution field )
            last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=int(aws_config.value["daysBack"]))

            if managed_product:
                # get the saved regions if the sync didn't run
                managed_product = managed_product[0]
                counter["managed_products"] += 1

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
                    last_execution = managed_product.lastExecution

            else:
                managed_product = db_client.create_managed_product(
                    name=service['service_name'], vendor_id=vendor_id,
                    managed_products_table=managed_products_table,
                    service_settings=aws_config.value
                )
                counter["new_managed_products"] += 1
                if managed_product:
                    active_managed_product_ids.append(managed_product.id)

        # ------------------------------------------------------------------------------------------------------------ #
        #                                              BUG SERVICE                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
            logger.info(f"'{service['service_name']}' - found active regions - {json.dumps(active_regions)}")

            # get all the health event for a given service
            service_health_events = health_client.describe_events(service=service["service_id"])
            # service_health_events = []
            if service_health_events:
                logger.info(
                    f"'{service['service_name']}' - {len(service_health_events)} health events retrieved | checking "
                    f"filtering conditions"
                )
                service_bugs = []
                for event in service_health_events:
                    # format and filter bug entries
                    bug = aws_api_client.format_bug_entry(
                        health_event=event, managed_product=managed_product, last_execution=last_execution,
                        active_regions=active_regions
                    )
                    if bug:
                        service_bugs.append(bug)
                    else:
                        counter["skipped_bugs"] += 1

                inserts = db_client.insert_bug_updates(
                    bugs=service_bugs, bugs_table=bugs_table, product_name=managed_product.name
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

            logger.info(f"'{managed_product.name}' - updating lastExecution")
            setattr(managed_product, 'lastExecution', datetime.datetime.utcnow())
            db_client.conn.commit()

        db_client.conn.commit()

        # remove managedProduct and linked bugs that don't have an active tagged aws resource
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
        if counter["inserted_bugs"]:
            message = f"{counter['inserted_bugs']} new bugs published"
        elif not counter["managed_products"]:
            message = 'There are no active and tagged aws services that match the vendor configuration'
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

    aws_api_client.bug_zero_vendor_status_update(
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
        {},
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "aws-bug-svc",
            "log_group_name": "aws-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )

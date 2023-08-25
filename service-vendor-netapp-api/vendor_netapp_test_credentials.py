#!/usr/bin/env python3
"""
created 2021-11-24
"""
import importlib
import inspect
import json
import logging.config
import os
import signal
import sys
import traceback

import boto3

from vendor_exceptions import LambdaTimeOutException, VendorExceptions
from vendor_netapp_bug_service import NetAppApiClient

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
    1. use event payload refresh token to generate a new set of access/refresh token
    2. save new refresh token in the service settings
    3. consume account customers endpoint and return to the consumer
    * if the authentication fails return an error indication to the consumer
    :return:
    """
    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    event = _args[0]
    vendor_id = "netapp"
    netapp_api_client = NetAppApiClient(
        vendor_id=vendor_id
    )

    logger.info(f"environment variables retrieved - {os.environ}")

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"
    service_error_msg = "username/password error"
    active_iq_customers_formatted = None
    refresh_token = ""
    try:
        # ------------------------------------------------------------------------------------------------------------ #
        #                                         NETAPP AUTHENTICATION FLOW                                           #
        # ------------------------------------------------------------------------------------------------------------ #
        logger.info(f"'{vendor_id}' - starting token retrieval process")
        api_tokens = netapp_api_client.generate_api_tokens_v2(
            refresh_token=event["refreshToken"],
        )
        refresh_token = api_tokens["refresh_token"]
        customers_endpoint = "https://api.activeiq.netapp.com/v1/system/list/level/customer"
        logger.info(f"'{vendor_id}' - getting Active QI customer IDs | {customers_endpoint}")
        active_iq_customers = netapp_api_client.consume_api(
            auth_token=api_tokens["access_token"], endpoint_url=customers_endpoint
        )
        active_iq_customers = active_iq_customers["customers"]["list"]
        active_iq_customers_formatted = [
            {"customerName": x["customer_name"], "customerId": x["customer_id"], "disabled": 0} for x in
            active_iq_customers
        ]
        active_iq_customers_formatted = sorted(active_iq_customers_formatted, key=lambda x: x["customerName"].title())

        message = f"validation completed successfully - {len(active_iq_customers)} activeIQ customers found"
        logger.info(message)
        service_error_msg = ""
        completed = True

    except (Exception, VendorExceptions, LambdaTimeOutException) as e:
        if isinstance(e, LambdaTimeOutException):
            error_type = "Program"
            severity = 1
        elif isinstance(e, VendorExceptions):
            error_type = "Operational"
            severity = 1
        else:
            error_type = "Program"
            severity = 1

        # if not VendorExceptions ( as we are testing tokens ) create a sns event
        if not isinstance(e, VendorExceptions):
            sns_client = boto3.client('sns')
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
        completed = False
        message = "authentication failed - check vendor API refresh token and try again"

    return {
        "message": message,
        "completed": completed,
        "service_error_msg": service_error_msg,
        "active_iq_customers": active_iq_customers_formatted,
        "refresh_token": refresh_token
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
    # get refresh token from the https://activeiq.netapp.com/api or from the settings table
    mock_event = {
        "refreshToken": ""
    }
    initiate(
        mock_event,
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-test-cred",
            "log_group_name": "netapp-test-cred",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )

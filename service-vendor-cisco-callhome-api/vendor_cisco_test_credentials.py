#!/usr/bin/env python3
"""
created 2021-08-26
# use credentials from context to test the the cisco auth method and return a status
"""
import importlib
import inspect
import json
import logging.config
import os
import signal
import sys
import time
import traceback

import boto3
from vendor_cisco_api_client import CiscoApiClient

from vendor_exceptions import LambdaTimeOutException

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

    :return:
    """
    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)
    event = _args[0]
    vendor_id = "cisco"
    cisco_api_client = CiscoApiClient(
        vendor_id=vendor_id
    )

    logger.info(f"environment variables retrieved - {os.environ}")
    credentials_name = ""
    service_error = ""
    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"

    try:
        # ------------------------------------------------------------------------------------------------------------ #
        #                                         CISCO AUTHENTICATION FLOW                                            #
        # ------------------------------------------------------------------------------------------------------------ #
        time.sleep(3)
        logger.info("starting auth process")
        # generate cisco service API oath auth ( for hardware inventory )
        credentials_name = "Cisco Service API Client Id / Client Secret"
        service_error = "service"
        cisco_api_client.generate_service_api_token(
            cisco_client_id=event["serviceApiClientId"],
            cisco_client_secret=event["serviceApiClientSecret"],
        )
        logger.info(f"{credentials_name} validation completed successfully")

        credentials_name = "Cisco Support API Client Id / Client Secret"
        service_error = "support"
        cisco_api_client.generate_support_api_tokens(
            cisco_client_id=event["supportApiClientId"],
            cisco_client_secret=event["supportApiClientSecret"],
        )
        logger.info(f"{credentials_name} validation completed successfully")

        message = f"auth flow completed"
        service_error = ""
        logger.info(message)
        completed = True

    except (ValueError, ConnectionError, NameError, LambdaTimeOutException) as e:

        if isinstance(e, LambdaTimeOutException):
            message = f"lambda instance has reached execution timeout"
            logger.error(f"{str(e)}")
            sns_client = boto3.client('sns')
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type="Program", severity=1,
                additional_info=additional_info,
                logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )

        elif isinstance(e, ConnectionError):
            logger.error(type(e))
            message = f"Vendor integration error - Cisco data APIs are not available"
            # generate an sn event record and send to the sns topic
            sns_client = boto3.client('sns')
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type="Operational", severity=1,
                additional_info=additional_info,
                logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )

        else:
            message = f"authentication failed - check {credentials_name}"
        completed = False

    return {
        "message": message,
        "completed": completed,
        "serviceError": service_error
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
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    mock_event = {
        "serviceApiClientId": "",
        "serviceApiClientSecret": "",
        "supportApiClientId": "",
        "supportApiClientSecret": ""
    }
    context = type("MockContext", (object,), {
        "log_stream_name": "test",
        "function_name": "cisco-test-cred",
        "log_group_name": "cisco-test-cred",
        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 3000
    })
    initiate(mock_event, context)

#!/usr/bin/env python3
"""
created 2022-01-31
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
from vendor_msft_api_client import MsftApiClient

from vendor_exceptions import LambdaTimeOutException, VendorExceptions

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
    vendor_id = "msft"
    msft_api_client = MsftApiClient(
        vendor_id=vendor_id
    )

    logger.info(f"environment variables retrieved - {os.environ}")
    error_msg = ""

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"
    try:
        # ------------------------------------------------------------------------------------------------------------ #
        #                                         MSFT AUTHENTICATION FLOW                                             #
        # ------------------------------------------------------------------------------------------------------------ #
        logger.info(f"'{vendor_id}' - starting auth process")
        # generate cisco service API oath auth ( for hardware inventory )
        error_msg = "username or password error"
        msft_api_client.gen_admin_dashboard_tokens(
            username=event["username"],
            password=event["password"],
        )
        message = f"'{vendor_id}' - validation completed successfully"
        logger.info(message)
        error_msg = ""
        completed = True

    except (VendorExceptions, LambdaTimeOutException, Exception) as e:
        message = str(e)
        if isinstance(e, LambdaTimeOutException):
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
            message = 'validation failed - internal server error | we are actively working on a fix'
        elif isinstance(e, VendorExceptions):
            message = 'validation failed - check user/password and try again'
            error_msg = message
        else:
            sns_client = boto3.client('sns')
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type="Operational", severity=1,
                additional_info=additional_info, logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )

        logger.error(str(message))
        completed = False

    return {
        "message": message,
        "completed": completed,
        "error_msg": error_msg,
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
    mock_event = {
        "username": "",
        "password": "",
    }
    test = initiate(
        mock_event,
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-test-cred-svc",
            "log_group_name": "msft-test-cred-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )
    logger.info(test)

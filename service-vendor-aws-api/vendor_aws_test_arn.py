#!/usr/bin/env python3
"""
created 2022-03-07
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
from botocore.exceptions import ClientError, ParamValidationError

from vendor_aws_api_client import AwsApiClient
from vendor_aws_health_client import HealthClient
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
    1. use event payload arn string to try and assume a role from another AWS Account
    2. Verify that the Role created provides access to
       a. AWS Health API
       b. AWS Cost Explorer API
    2. return payload with indication if
       a. role exists
       b. AWS Health API access granted
       c. AWS Cost Explorer API access granted
    :return:
    """
    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    event = _args[0]
    vendor_id = "aws"
    aws_api_client = AwsApiClient(
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
    validation_status = {
        "roleAssumed": False, "costExplorerApiAccess": False, "healthApiAccess": False,
        "costExplorerApiAccessErrorMessage": "", "healthApiAccessErrorMessage": ""
    }
    try:
        logger.info(f"'{vendor_id}' - starting assume role process")
        role_arn = event["awsApiHealthApiRoleArn"]
        assumed_role_object = aws_api_client.sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="AWSHealthCrossAccountSession"
        )
        validation_status['roleAssumed'] = True
        logger.info(f"'{vendor_id}' - validating aws cost explorer api access")
        try:
            cost_explorer_api = boto3.client(
                'ce',
                aws_access_key_id=assumed_role_object['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed_role_object['Credentials']['SecretAccessKey'],
                aws_session_token=assumed_role_object['Credentials']['SessionToken']
            )
            cost_explorer_api.get_dimension_values(
                TimePeriod={
                    'Start': (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                    'End': (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).strftime("%Y-%m-%d")
                },
                Dimension="SERVICE"
            )
            validation_status["costExplorerApiAccess"] = True

        except (ClientError, ParamValidationError) as e:
            logger.info(f"'{vendor_id}' - cost explore api validation failed | {str(e)}")
            validation_status["costExplorerApiAccessErrorMessage"] = str(e)

        logger.info(f"'{vendor_id}' - validating aws health api access")
        try:
            HealthClient(
                aws_access_key_id=assumed_role_object['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed_role_object['Credentials']['SecretAccessKey'],
                aws_session_token=assumed_role_object['Credentials']['SessionToken']
            )
            validation_status["healthApiAccess"] = True
        except (ClientError, ParamValidationError) as e:
            logger.info(f"'{vendor_id}' - health api validation failed | {str(e)}")
            validation_status["healthApiAccessErrorMessage"] = str(e)

        message = f"validation completed - {json.dumps(validation_status)}"
        logger.info(message)

    except (Exception, VendorExceptions, LambdaTimeOutException) as e:
        if isinstance(e, LambdaTimeOutException):
            error_type = "Program"
            severity = 1
        elif isinstance(e, (VendorExceptions, ParamValidationError, ClientError)):
            error_type = "Operational"
            severity = 1
        else:
            error_type = "Program"
            severity = 1
        # if not VendorExceptions ( as we are testing tokens ) create a sns event
        if not isinstance(e, VendorExceptions) and not isinstance(e, ParamValidationError) and not \
                isinstance(e, ClientError):
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

    return validation_status


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
        "awsApiHealthApiRoleArn": ""
    }
    initiate(
        mock_event,
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "aws-test-arn",
            "log_group_name": "aws-test-arn",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )

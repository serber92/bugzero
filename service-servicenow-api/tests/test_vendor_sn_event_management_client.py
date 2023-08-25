"""
unit tests for db_client.py
"""
import json
import os
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_requests_read_timeout


class Test(TestCase):
    """
    main test class
    """
    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                    handler                                                       #
    # ---------------------------------------------------------------------------------------------------------------- #

    @patch.dict(os.environ, mock_env())
    def test_handler_missing_records_field(*_args):
        """
        requirement: the service only works with SNS events passing a 'Records' list in the event object
        mock: event object with non-sns event missing the records field
        description: the function should return a json with an error_message =
                     "missing 'Records' field in event object..."
        more information: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
        :param _args:
        :return:
        """
        event = {
            "Other-Non-Records-Field": [
                {
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "99999",
                    "EventSource": "aws:non-sns",
                }
            ]
        }
        from vendor_sn_event_management_client import handler
        process = json.loads(handler(event=event)["message"])
        assert process["success"] is False and "missing 'Records' field in event object" in process["error_message"]

    @patch.dict(os.environ, mock_env())
    def test_handler_wrong_records_type(*_args):
        """
        requirement: the service only works with SNS events
        mock: event object with non-sns event and a wrong records object passed in the events
        description: the function should return a json with an error_message =
                     "events object type must be one of [dict(array), lis] not....."
        more information: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
        :param _args:
        :return:
        """
        event = {
            "Records": 10
        }
        from vendor_sn_event_management_client import handler
        process = json.loads(handler(event=event)["message"])
        assert process["success"] is False and "Records object type must be one of [dict(array), list] not" \
            in process["error_message"]

    @patch.dict(os.environ, mock_env())
    def test_handler_wrong_event_type(*_args):
        """
        requirement: the service only works with SNS events
        mock: context object with non-sns event description
        description: the function should return a json with an error_message =
                     "events object type must be one of [dict(array), lis] not....."
        more information: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
        :param _args:
        :return:
        """
        event = {
            "Records": [
                {
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "test",
                    "EventSource": "aws:non-sns",
                    "Sns": {
                        "SignatureVersion": "1",
                        "Timestamp": "2019-01-02T12:45:07.000Z",
                        "Signature": "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
                        "SigningCertUrl": "test",
                        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                        "Message": "Hello from SNS!",
                        "MessageAttributes": {
                            "Test": {
                                "Type": "String",
                                "Value": "TestString"
                            },
                            "TestBinary": {
                                "Type": "Binary",
                                "Value": "TestBinary"
                            }
                        },
                        "Type": "Notification",
                        "UnsubscribeUrl": "test",
                        "TopicArn": "arn:aws:sns:us-east-2:123456789012:sns-lambda",
                        "Subject": "TestInvoke"
                    }
                }
            ]
        }
        from vendor_sn_event_management_client import handler
        process = json.loads(handler(event=event)["message"])
        assert process["success"] is False and \
            process["error_message"] == 'not supported or missing EventSource - aws:non-sns'

    @patch.dict(os.environ, mock_env())
    @patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
    def test_handler_endpoint_error(*_args):
        """
        requirement: post error events to sn endpoint
        mock: requests object with status code 404
        description: all post tries failed due to an endpoint error should, returned message should have the success
                     field set to False
        :param _args:
        :return:
        """
        event = {
            "Records": [
                {
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "test",
                    "EventSource": "aws:sns",
                    "Sns": {
                        "SignatureVersion": "1",
                        "Timestamp": "2019-01-02T12:45:07.000Z",
                        "Signature": "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
                        "SigningCertUrl": "test",
                        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                        "Message": json.dumps({"test_record": 1}),
                        "MessageAttributes": {
                            "Test": {
                                "Type": "String",
                                "Value": "TestString"
                            },
                            "TestBinary": {
                                "Type": "Binary",
                                "Value": "TestBinary"
                            }
                        },
                        "Type": "Notification",
                        "UnsubscribeUrl": "test",
                        "TopicArn": "arn:aws:sns:us-east-2:123456789012:sns-lambda",
                        "Subject": "TestInvoke"
                    }
                }
            ]
        }
        from vendor_sn_event_management_client import handler
        process = json.loads(handler(event=event)["message"])
        assert process["success"] is False and \
            process["error_message"] == 'one or more events failed to be published through the endpoint'

    @patch.dict(os.environ, mock_env())
    @patch('requests.post', lambda **_kwargs: mock_requests_read_timeout())
    def test_handler_request_error(*_args):
        """
        requirement: post error events to sn endpoint
        mock: requests exception
        description: all post tries failed due to a request exception, returned message should have the success
                     field set to False
        :param _args:
        :return:
        """
        event = {
            "Records": [
                {
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "test",
                    "EventSource": "aws:sns",
                    "Sns": {
                        "SignatureVersion": "1",
                        "Timestamp": "2019-01-02T12:45:07.000Z",
                        "Signature": "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
                        "SigningCertUrl": "test",
                        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                        "Message": json.dumps({"test_record": 1}),
                        "MessageAttributes": {
                            "Test": {
                                "Type": "String",
                                "Value": "TestString"
                            },
                            "TestBinary": {
                                "Type": "Binary",
                                "Value": "TestBinary"
                            }
                        },
                        "Type": "Notification",
                        "UnsubscribeUrl": "test",
                        "TopicArn": "arn:aws:sns:us-east-2:123456789012:sns-lambda",
                        "Subject": "TestInvoke"
                    }
                }
            ]
        }
        from vendor_sn_event_management_client import handler
        process = json.loads(handler(event=event)["message"])
        assert process["success"] is False and \
            process["error_message"] == 'one or more events failed to be published through the endpoint'

    @patch.dict(os.environ, mock_env())
    @patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test"}))
    def test_handler_events_list(*_args):
        """
        requirement: post a list of events to sn endpoint
        mock: list of events inside the event["Sns"]["Message"], requests object with status code 200
        description: some services ( e.g msft ) can chain event in a list and send it to SNS as one record, ensure that
                     a correct iteration process over a single sns message containing multiple events
        :param _args:
        :return:
        """
        event = {
            "Records": [
                {
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "test",
                    "EventSource": "aws:sns",
                    "Sns": {
                        "SignatureVersion": "1",
                        "Timestamp": "2019-01-02T12:45:07.000Z",
                        "Signature": "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
                        "SigningCertUrl": "test",
                        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                        "Message": json.dumps([{"test_record": 2}, {"test_record": 2}, {"test_record": 2}]),
                        "MessageAttributes": {
                            "Test": {
                                "Type": "String",
                                "Value": "TestString"
                            },
                            "TestBinary": {
                                "Type": "Binary",
                                "Value": "TestBinary"
                            }
                        },
                        "Type": "Notification",
                        "UnsubscribeUrl": "test",
                        "TopicArn": "arn:aws:sns:us-east-2:123456789012:sns-lambda",
                        "Subject": "TestInvoke"
                    }
                }
            ]
        }
        from vendor_sn_event_management_client import handler
        process = json.loads(handler(event=event)["message"])
        assert process["success"]

"""
unit tests for vendor_netapp_test_credentials.py
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_vendor_connection_exception


########################################################################################################################
#                                                     initiate                                                         #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'vendor_netapp_api_client.NetAppApiClient.generate_api_tokens', lambda *args, **kwargs: {"access_token": "test"}
)
@patch('vendor_netapp_api_client.NetAppApiClient.consume_api', lambda *args, **kwargs: {"customers": {"list": []}})
def test_initiate_success(*_args):
    """
    requirement: use credentials from context to testing the the netapp auth method and return a status
    mock: NetAppApiClient, generate_support_api_tokens, generate_service_api_token
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_netapp_test_credentials import initiate
    mock_event = {
        "username": "",
        "password": "",
    }
    execution = initiate(
        mock_event,
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-test-cred",
            "log_group_name": "netapp-test-cred",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )

    assert execution["completed"] is True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_test_credentials']
    del sys.modules['vendor_netapp_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'vendor_netapp_api_client.NetAppApiClient.generate_api_tokens',
    lambda *args, **kwargs: mock_vendor_connection_exception()
)
@patch('vendor_netapp_api_client.NetAppApiClient.consume_api', lambda *args, **kwargs: {"customers": {"list": []}})
def test_initiate_connection_error(*_args):
    """
    requirement: use credentials from context for testing the the netapp auth method and return a status
    mock: NetAppApiClient, generate_support_api_tokens, generate_service_api_token
    description: VendorConnectionError resulting in a credentials testing error

    :param _args:
    :return:
    """
    from vendor_netapp_test_credentials import initiate
    mock_event = {
        "username": "",
        "password": "",
    }
    execution = initiate(
        mock_event,
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-test-cred",
            "log_group_name": "netapp-test-cred",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )
    assert not execution["completed"]
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_test_credentials']
    del sys.modules['vendor_netapp_api_client']

"""
unit tests for vendor_vmware_test_credentials.py
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_bad_credentials_verification_event, \
    mock_good_credentials_verification_event, mock_connection_error, mock_connect_name_error


########################################################################################################################
#                                                     initiate                                                         #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch(
    'vendor_cisco_api_client.CiscoApiClient',
    lambda **_kwargs: type("mockApiClient", (object,),
                           {"generate_service_api_token": lambda *_args, **_kwargs: [True, True],
                            "generate_support_api_tokens": lambda *_args, **_kwargs: [True, True]})
)
def test_initiate_success(*_args):
    """
    requirement: use credentials from context to test the the cisco auth method and return a status
    mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_cisco_test_credentials import initiate
    assert initiate(
        mock_good_credentials_verification_event
    )["completed"] is True
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_test_credentials']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch('vendor_cisco_api_client.CiscoApiClient.generate_service_api_token', mock_connection_error)
def test_initiate_connection_error(*_args):
    """
    requirement: use credentials from context to test the the cisco auth method and return a status
    mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
    description: test a failed request due to api connection error returning
                 "Vendor integration error - Cisco data APIs are not available" message field value

    :param _args:
    :return:
    """
    from vendor_cisco_test_credentials import initiate
    assert initiate(
        mock_bad_credentials_verification_event
    )["message"] == "Vendor integration error - Cisco data APIs are not available"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_test_credentials']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch('vendor_cisco_api_client.CiscoApiClient.generate_service_api_token', mock_connect_name_error)
def test_initiate_credentials_error(*_args):
    """
        requirement: use credentials from context to test the the cisco auth method and return a status
    mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
    description: test a failed request due to api bad credentials returning
                 "authentication failed - check Cisco Service API Client Id / Client Secret"
    :param _args:
    :return:
    """
    from vendor_cisco_test_credentials import initiate
    assert initiate(
        mock_bad_credentials_verification_event
    )["message"] == "authentication failed - check Cisco Service API Client Id / Client Secret"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_test_credentials']

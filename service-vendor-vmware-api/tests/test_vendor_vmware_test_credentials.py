"""
unit tests for vendor_vmware_test_credentials.py
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_bad_credentials_verification_event, \
    mock_bad_good_credentials_verification_event


########################################################################################################################
#                                                   initiate TESTS                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
def test_initiate_success(*_args):
    """
    test a simple initiate with valid credentials test
    :return:
    """
    with patch(
            'vendor_vmware_api_client.VmwareApiClient',
            lambda **_kwargs: type("hello", (object,), {"get_auth_token": lambda *_args, **_kwargs: [True, True]})
    ):
        from vendor_vmware_test_credentials import initiate
        assert initiate(
            mock_bad_good_credentials_verification_event
        )["completed"] is True
        # remove mocks import to prevent interference with other tests
        del sys.modules['db_client']
        del sys.modules['vendor_vmware_api_client']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
def test_initiate_org_id_error(*_args):
    """
    test a failed request due to bad orgId
    :param _args:
    :return:
    """
    with patch('vendor_vmware_api_client.VmwareApiClient'):
        from vendor_vmware_test_credentials import initiate
        assert initiate(
            mock_bad_credentials_verification_event
        )["message"] == "Validation failed - check orgId and try again"
        # remove mocks import to prevent interference with other tests
        del sys.modules['db_client']
        del sys.modules['vendor_vmware_api_client']

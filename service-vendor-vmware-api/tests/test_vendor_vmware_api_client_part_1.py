"""
unit tests for vendor_vmware_api_client
"""
import json
import os
import sys
from unittest import TestCase
from unittest.mock import patch

from botocore.exceptions import ClientError

from tests.external_dependencies import mock_env, mock_response_instance, MockVmwareApiInstance, \
    mock_collector_status_response_healthy, MockSecrectManagerClient


class Test(TestCase):
    """
    testing class
    """
########################################################################################################################
#                                                     init                                                             #
########################################################################################################################
    @patch.dict(os.environ, mock_env())
    @patch('download_manager.request_instance', mock_response_instance(response_text="nonJson"))
    def test_init_instantiate(*_args):
        """
        api status response: False
        raise ConnectionError
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient(vendor_id="vmware")
            assert True
        except ConnectionError:
            assert True

        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                               check_collectors_health                                                #
########################################################################################################################
    @patch.dict(os.environ, mock_env())
    @patch('download_manager.request_instance', mock_response_instance(response_text="nonJson"))
    def test_check_collectors_health_failed(*_args):
        """
        api status response: False
        raise ConnectionError
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.check_collectors_health(MockVmwareApiInstance(), service_token=True)
            assert False
        except ConnectionError:
            assert True

        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text=mock_collector_status_response_healthy
        )
    )
    def test_check_collectors_healthy_response(*_args):
        """
        api status response status is healthy ( > 0 )
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.check_collectors_health(MockVmwareApiInstance(), service_token=True) > 0
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            return_false=True, response_text=""
        )
    )
    def test_check_collectors_health_connection_error(*_args):
        """
        skyline collector healthy endpoint is raising ConnectionError
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.check_collectors_health(MockVmwareApiInstance(), service_token=True)
            assert False
        except ConnectionError:
            assert True
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                               get_oath_cred                                                          #
########################################################################################################################
    def test_get_oath_cred_success(*_args):
        """
        test a successful oauth retrieval from AWS SecretManager ( mock )
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_oath_cred(
            MockSecrectManagerClient(secret_binary=True), secret_name=True, secret_fields=True
        ) == bytes({})
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    def test_get_oath_client_error(*_args):
        """
        test an exception ClientError from AWS SecretManager ( mock )
        raise ClientError
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.get_oath_cred(
                MockSecrectManagerClient(binary_error=True, secret_binary=True), secret_name=True, secret_fields=True
            )
            assert False
        except ClientError:
            assert True
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    def test_get_oath_secret_fields(*_args):
        """
        test an exception where the SecretManager secret is missing secret fields that should be stored
        raise ClientError
        :return:
        """
        # test a db operational error
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.get_oath_cred(
                MockSecrectManagerClient(secret_string={"test": ""}), secret_name=True, secret_fields=["missing_field"]
            )
            assert False
        except ValueError:
            assert True
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                                   get_auth_token                                                     #
########################################################################################################################
    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text=mock_collector_status_response_healthy,
            return_false=True
        )
    )
    def test_get_auth_token_bad_response(*_args):
        """
        test an empty response from the request_instance
        raise ValueError
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.get_auth_token(
                MockVmwareApiInstance(), vmware_org_id="", vmware_cs_password="", vmware_cs_username=""
            )
            assert False
        except ValueError:
            assert True
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text=json.dumps({"idpLoginUrl": ""}),
        )
    )
    def test_get_auth_token_xpath_index_error(*_args):
        """
        test xpath index error
        background - a few of the auth stages require variables found with xpath, an index error should be handled when
        the xpath lookup fail
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_auth_token(
            MockVmwareApiInstance(), vmware_org_id="", vmware_cs_password="", vmware_cs_username="") is False
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

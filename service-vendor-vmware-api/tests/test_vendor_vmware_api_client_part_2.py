"""
unit tests for vendor_vmware_api_client
"""
import json
import sys
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_response_instance, MockVmwareApiInstance, \
    mock_skyline_rule_list, \
    MockDbClientManagedProductsEmpty


class Test(TestCase):
    """
    testing class part 2/2
    """
########################################################################################################################
#                                                   get_skyline_bugs                                                   #
########################################################################################################################
    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="",
        )
    )
    def test_get_skyline_bugs_connection_error(*_args):
        """
        test an empty response from from skyline API, returning empty list
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_skyline_bugs(
                MockVmwareApiInstance(), auth_token="", prod_id="", last_execution="", org_id="", morid=""
            ) == []
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="nonJso",
        )
    )
    def test_get_skyline_bugs_response_error(*_args):
        """
        test a decode error for response text received from skyline
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_skyline_bugs(
            MockVmwareApiInstance(), auth_token="", prod_id="", last_execution="", org_id="", morid=""
        ) == []
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text=json.dumps({"ruleList": [], "totalCount": 0}),
        )
    )
    def test_get_skyline_bugs_no_findings(*_args):
        """
        test a successful consume of the API with 0 findings in skyline ( bugs = [] )
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_skyline_bugs(
            MockVmwareApiInstance(), auth_token="", prod_id="", last_execution="", org_id="", morid=""
        ) == []
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text=mock_skyline_rule_list),
    )
    def test_get_skyline_bugs_w_finding(*_args):
        """
        test a successful consume of the API with 1 finding in skyline ( len VmwareApiClient.get_skyline_bugs()  == 1 )
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert len(VmwareApiClient.get_skyline_bugs(
            MockVmwareApiInstance(), auth_token="", prod_id="", last_execution="", org_id="", morid=""
        )) == 1
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text=json.dumps({"ruleList": [], "totalCount": 2}),
        )
    )
    def test_get_skyline_bugs_additional_pages(*_args):
        """
        test a successful consume of the API with pagination that requires more requests
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_skyline_bugs(
            MockVmwareApiInstance(), auth_token="", prod_id="", last_execution="", org_id="", morid="", page_size=1
        ) == []
        # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                                   get_inventory                                                      #
########################################################################################################################
    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="", return_false=True
        )
    )
    def test_get_inventory_connection_error(*_args):
        """
        test an empty response from skyline API handling connectionError
        raise ConnectionError
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.get_inventory(MockVmwareApiInstance(), auth_token="", org_id="")
            assert False
        except ConnectionError:
            assert True
            # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="nonJson"
        )
    )
    def test_get_inventory_json_error(*_args):
        """
        test response text error from skyline API handling JSONDecodeError
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        try:
            VmwareApiClient.get_inventory(MockVmwareApiInstance(), auth_token="", org_id="")
            assert False
        except ConnectionError:
            assert True
            # remove mocks import to prevent interference with other tests
        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="[]"
        )
    )
    def test_get_inventory(*_args):
        """
        test a successful inventory response from skyline API ( empty list )
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        assert VmwareApiClient.get_inventory(MockVmwareApiInstance(), auth_token="", org_id="") == []

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                                   get_kb_data                                                        #
########################################################################################################################
    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="[]"
        )
    )
    def test_get_kb_data_cached_Kb(*_args):
        """
        skip consuming the vmware KB API when a kb is already cached
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        kb_id = "kb-id-test"
        cached_kb_data = {kb_id: {True}}
        assert VmwareApiClient.get_kb_data(MockVmwareApiInstance(cached_kb_data=cached_kb_data), kb_id=kb_id)

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="[]", return_false=True
        )
    )
    def test_get_kb_data_request_failed(*_args):
        """
        test api connection error
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        kb_id = "kb-id-test"
        cached_kb_data = {}
        assert not VmwareApiClient.get_kb_data(
            MockVmwareApiInstance(cached_kb_data=cached_kb_data, overwrite_kb_data=True), kb_id=kb_id
        )

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text="nonJson"
        )
    )
    def test_get_kb_data_json_decode_error(*_args):
        """
        test a text response with bad json from skyline API
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        kb_id = "kb-id-test"
        cached_kb_data = {}
        assert not VmwareApiClient.get_kb_data(
            MockVmwareApiInstance(cached_kb_data=cached_kb_data, overwrite_kb_data=True), kb_id=kb_id
        )

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

    @patch(
        'download_manager.request_instance', mock_response_instance(
            response_text='{"kb_id": "kb-id-test"}'
        )
    )
    def test_get_kb_data(*_args):
        """
        test a text response with bad json from skyline API
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        kb_id = "kb-id-test"
        cached_kb_data = {}
        kb_id_return = VmwareApiClient.get_kb_data(
            MockVmwareApiInstance(cached_kb_data=cached_kb_data, overwrite_kb_data=True), kb_id=kb_id
        )
        assert kb_id_return["kb_id"] == kb_id

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                                   bug_search_filters                                                 #
########################################################################################################################
    def test_bug_search_filters(*_args):
        """
        test a text response with bad json from skyline API
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        test_case = VmwareApiClient.bug_search_filters(
            page=10, page_size=100, first_seen="", morid="343243"
        )
        assert isinstance(test_case, dict)

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

########################################################################################################################
#                                           bug_zero_vendor_status_update                                              #
########################################################################################################################
    def test_bug_zero_vendor_status_update(*_args):
        """
        test a text response with bad json from skyline API
        :return:
        """
        from vendor_vmware_api_client import VmwareApiClient
        cached_kb_data = {}
        assert not VmwareApiClient.bug_zero_vendor_status_update(
            MockVmwareApiInstance(cached_kb_data=cached_kb_data, overwrite_kb_data=True),
            db_client=MockDbClientManagedProductsEmpty, started_at="", services_table="services_table",
            service_execution_table="service_execution_table", service_status="", vendor_id="", service_id="",
            service_name="", error=0, message=""
        )

        del sys.modules['download_manager']
        del sys.modules['vendor_vmware_api_client']

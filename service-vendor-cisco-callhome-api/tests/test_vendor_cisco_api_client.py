"""
unit tests for vendor_vmware_api_client
"""
import json
import os
import sys
from unittest.mock import patch

from botocore.exceptions import ClientError

from tests.external_dependencies import mock_env, mock_requests_connection_error, MockSecrectManagerClient, \
    MockDbClientManagedProductsEmpty, MockDbClientExistingServiceEntry


########################################################################################################################
#                                                     init                                                             #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_init_instantiate(*_args):
    """
    api status response: False
    raise ConnectionError
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    assert instance.vendor_id == "cisco"

    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                               generate_service_api_token                                             #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": json.dumps({"error": True})})
)
def test_generate_service_api_token_authentication_error(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: mock a server json response indicating an error,
                ConnectionError("Unsupported Client Authentication type.")  should be raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.generate_service_api_token(self=instance, cisco_client_id="", cisco_client_secret="")
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": "non-json-string"})
)
def test_generate_service_api_token_json_decode_error(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: mock a non-json server response indicating a cisco API error ,
                ConnectionError("Vendor integration error - Cisco data APIs are not available") should be raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.generate_service_api_token(self=instance, cisco_client_id="", cisco_client_secret="")
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance', mock_requests_connection_error
)
def test_generate_service_api_token_connection_error(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: mock a cisco API connection error ,
                ConnectionError("Vendor integration error - Cisco data APIs are not available") should be raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.generate_service_api_token(self=instance, cisco_client_id="", cisco_client_secret="")
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": json.dumps({"valid-json_response": ""})})
)
def test_generate_service_api_token(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: ensure that a successful response returns a valid dict object
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    token_dict_object = CiscoApiClient.generate_service_api_token(
        self=instance, cisco_client_id="", cisco_client_secret=""
    )
    assert isinstance(token_dict_object, dict)

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                              generate_support_api_tokens                                             #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": "non-json-string"})
)
def test_generate_support_api_tokens_json_decode_error(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: mock a non-json server response indicating a cisco API error ,
                ConnectionError("Vendor integration error - Cisco data APIs are not available") should be raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.generate_support_api_tokens(self=instance, cisco_client_id="", cisco_client_secret="")
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance', mock_requests_connection_error
)
def test_generate_support_api_tokens_connection_error(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: mock a cisco API connection error ,
                ConnectionError("Vendor integration error - Cisco data APIs are not available") should be raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.generate_support_api_tokens(self=instance, cisco_client_id="", cisco_client_secret="")
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": json.dumps({"valid-json_response": ""})})
)
def test_generate_support_api_token(*_args):
    """
    requirement: retrieve authentication tokens using valid cisco user/pass
    mock: cisco_client_id, cisco_client_secret, download_instance
    description: ensure that a successful response returns a valid dict object
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    token_dict_object = CiscoApiClient.generate_support_api_tokens(
        self=instance, cisco_client_id="", cisco_client_secret=""
    )
    assert isinstance(token_dict_object, dict)

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                              get_hardware_inventory                                                  #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": "non-json-string"})
)
def test_get_hardware_inventory_json_decode_error(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service API
    mock: cisco_customer_id, cisco_service_token, download_instance
    description: mock a non-json server response indicating a cisco API error ,
                ConnectionError("Vendor API error - can't get vendor inventory") should be raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.get_hardware_inventory(
            self=instance, cisco_customer_id="", cisco_service_token={"token_type": "", "access_token": ""}
        )
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": json.dumps({"other-schema": ""})})
)
def test_get_hardware_inventory_json_schema_is_different(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service API
    mock: cisco_customer_id, cisco_service_token, download_instance
    description: mock a server json response missing the data field indicating a cisco API error,
                a ConnectionError("Vendor API error - can't get vendor inventory") should be re-raised from a KeyError()
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.get_hardware_inventory(
            self=instance, cisco_customer_id="", cisco_service_token={"token_type": "", "access_token": ""}
        )
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance', mock_requests_connection_error
)
def test_get_hardware_inventory_connection_error(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service APIs
    mock: cisco_customer_id, cisco_service_token, download_instance
    description: mock a cisco API connection error when trying to retrieve inventory,
                 ConnectionError("Vendor API error - can't get vendor inventory") should be raised from the original
                 ConnectionError
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.get_hardware_inventory(
            self=instance, cisco_customer_id="", cisco_service_token={"token_type": "", "access_token": ""}
        )
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": json.dumps({"data": {"inventory": []}})})
)
def test_get_hardware_inventory(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service APIs
    mock: cisco_customer_id, cisco_service_token, download_instance
    description: ensure that a successful response returns a valid dict object
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    token_dict_object = CiscoApiClient.get_hardware_inventory(
        self=instance, cisco_customer_id="", cisco_service_token={"token_type": "", "access_token": ""}
    )
    assert isinstance(token_dict_object, dict)

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                               get_oath_cred                                                          #
########################################################################################################################
def test_get_oath_cred_success(*_args):
    """
    requirement: retrieve cisco oath per service_secret_id from AWS Secrets Manager
    mock: AWS secret manager client, secret_string
    description: ensure that the secret is returned as a dict object
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    assert CiscoApiClient.get_oath_cred(
        MockSecrectManagerClient(secret_binary=True,secret_string=json.dumps({"ClientId": "Test"})),
        secret_name=True
    )['ClientId'] == 'Test'
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_cisco_api_client']
    del sys.modules['download_manager']


def test_get_oath_cred_missing_secret(*_args):
    """
    requirement: retrieve cisco oath per service_secret_id from AWS Secrets Manager
    mock: AWS secret manager client, secret_string
    description: the required 'ClientId' field is missing from the secret ensure that an
    Exception("AWS secret error - ClientId is missing or empty") is raised
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    try:
        CiscoApiClient.get_oath_cred(
            MockSecrectManagerClient(secret_binary=True,secret_string=json.dumps({"wrong-field": "Test"})),
            secret_name=True
        )
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_cisco_api_client']
    del sys.modules['download_manager']


def test_get_oath_client_error(*_args):
    """
    requirement: retrieve cisco oath per service_secret_id from AWS Secrets Manager
    mock: AWS secret manager client, clientError exception
    description: ensure that a ClientError is raised
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    try:
        CiscoApiClient.get_oath_cred(MockSecrectManagerClient(binary_error=True, secret_binary=True), secret_name=True)
        assert False
    except ClientError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_cisco_api_client']
    del sys.modules['download_manager']


########################################################################################################################
#                                               get_service_api_customer_id                                            #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs: type("mockResponse", (object,), {"text": "non-json-string"})
)
def test_get_service_api_customer_id_json_decode_error(*_args):
    """
    requirement: retrieve customer_id using valid cisco user/pass
    mock: cisco_service_token, download_instance
    description: mock a non-json server response indicating a cisco API error ,
                 ConnectionError("Vendor API error - can't get account information") should be raised from a the
                 original JSONDecodeError
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.get_service_api_customer_id(
            self=instance, cisco_service_token={"token_type": "", "access_token": ""}
        )
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('download_manager.download_instance', mock_requests_connection_error)
def test_get_service_api_customer_id_connection_error(*_args):
    """
    requirement: retrieve customer_id using valid cisco user/pass
    mock: cisco_service_token, download_instance
    description: mock a cisco API connection error ,
                 ConnectionError("Vendor API error - can't get account information") should be raised from a the
                 original ConnectionError
    :return:
    """
    # test a db operational error
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        CiscoApiClient.get_service_api_customer_id(
            self=instance, cisco_service_token={"token_type": "", "access_token": ""}
        )
        assert False
    except ConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                           bug_zero_vendor_status_update                                              #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_bug_zero_vendor_status_update(*_args):
    """
    requirement: execute bug_zero_vendor_status_update successfully
    mock: db_client, **kwargs for bug_zero_vendor_status_update
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    assert not instance.bug_zero_vendor_status_update(
        db_client=MockDbClientManagedProductsEmpty, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )

    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
def test_bug_zero_vendor_status_update_new_entry(*_args):
    """
    requirement: execute bug_zero_vendor_status_update successfully
    mock: db_client, **kwargs for bug_zero_vendor_status_update
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    assert not instance.bug_zero_vendor_status_update(
        db_client=MockDbClientExistingServiceEntry, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )

    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                           bugs_by_prod_family_and_sv                                              #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('download_manager.download_instance', lambda *_args, **_kwargs: False)
def test_bugs_by_prod_family_and_sv_connection_error(*_args):
    """
    requirement: retrieve bugs for a given cisco product family name and affected software versions
    mock: CiscoApiClient instance, download_instance, **kwargs ugs_by_prod_family_and_sv
    description: a mocked failed download_instance should result in a
    ConnectionError("Vendor integration error - Cisco data APIs are not available") being raised
    :return:
    """
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        instance.bugs_by_prod_family_and_sv(
            cisco_service_token={"token_type": "", "access_token": ""}, product_family_name="", managed_product_id=1,
            products=[
                {"swVersion": "1"},
                {"swVersion": "2"}
            ],
            severities=["1"],
            vendor_bug_statuses="", earliest_bug_date=""
        )
        assert False
    except ConnectionError:
        assert True
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs:
    type("mockResponse", (object,), {"text": json.dumps({"pagination_response_record": {"total_records": 0}})})
)
def test_bugs_by_prod_family_thread_error(*_args):
    """
    requirement: retrieve bugs for a given cisco product family name and affected software versions
    mock: CiscoApiClient instance, download_instance, threadError, **kwargs ugs_by_prod_family_and_sv
    description: pagination is downloaded using a multi-threaded manager than can log errors to the main class
                 enumerating self.thread_error_tracker, when the download thread are exited the thread is check and if
                 self.thread_error_tracker != 0, a ConnectionError should be raised
    :return:
    """
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    # set the thread_error_tracker to 1 to force a connection error
    instance.thread_error_tracker = 1
    try:
        instance.bugs_by_prod_family_and_sv(
            cisco_service_token={"token_type": "", "access_token": ""}, product_family_name="", managed_product_id=1,
            products=[
                {"swVersion": "1"},
                {"swVersion": "2"}
            ],
            severities=["1"],
            vendor_bug_statuses="", earliest_bug_date=""
        )
        assert False
    except ConnectionError:
        assert True
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs:
    type("mockResponse", (object,),
         {"text": json.dumps(
             {"pagination_response_record": {"total_records": 1, "last_index": 1},
              "bugs": [
                  {"bug_id": 1, "last_modified_date": "2021-09-27", "status": "1", "products": []}
              ]
              }
         )
         }
         )
)
def test_bugs_by_prod_family_bug_index_error(*_args):
    """
    requirement: retrieve bugs for a given cisco product family name and affected software versions
    mock: CiscoApiClient instance, download_instance, threadError, **kwargs ugs_by_prod_family_and_sv
    description: ensure that an KeyError in a given bug is converted to a
                 ConnectionError("Vendor integration error - Cisco data APIs are not available")
    :return:
    """
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    try:
        instance.bugs_by_prod_family_and_sv(
            cisco_service_token={"token_type": "", "access_token": ""}, product_family_name="", managed_product_id=1,
            products=[
                {"swVersion": "1"},
                {"swVersion": "2"}
            ],
            severities=["1"],
            vendor_bug_statuses=["1"],
            earliest_bug_date=""
        )
        assert False
    except KeyError:
        assert True
    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *_args, **_kwargs:
    type("mockResponse", (object,),
         {"text": json.dumps(
             {"pagination_response_record": {"total_records": 1, "last_index": 1},
              "bugs": [
                  {"bug_id": 1, "last_modified_date": "2021-09-27", "status": "1", "products": []}
              ]
              }
         )
         }
         )
)
def test_bugs_by_prod_family(*_args):
    """
    requirement: retrieve bugs for a given cisco product family name and affected software versions
    mock: CiscoApiClient instance, download_instance, threadError, **kwargs ugs_by_prod_family_and_sv
    description: test a successful execution resulting in 1 new bug
    :return:
    """
    from vendor_cisco_api_client import CiscoApiClient
    instance = CiscoApiClient(vendor_id="cisco")
    assert len(instance.bugs_by_prod_family_and_sv(
        cisco_service_token={"token_type": "", "access_token": ""}, product_family_name="", managed_product_id=1,
        products=[
            {"swVersion": "1", "serialNumber": "111111"},
            {"swVersion": "2", "serialNumber": "222222"}
        ],
        severities=["1"],
        vendor_bug_statuses=["1"],
        earliest_bug_date=""
    )) == 1

    del sys.modules['download_manager']
    del sys.modules['vendor_cisco_api_client']

"""
unit test fro vendor_vmware_bug_service
"""
import datetime
import os
import sys
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from tests.external_dependencies import mock_env, mock_operational_error, MockEmptyDbClient, \
    MockDbClientNoExistingBugs, MockDbClientOperationalError, MockDbClientSkipManagedProducts, \
    mock_connection_error, mock_connect_name_error


########################################################################################################################
#                                                   initiate                                                           #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_cisco_bug_service.cisco_authentication', mock_operational_error)
@patch('vendor_cisco_api_client.CiscoApiClient')
@patch('db_client.Database', MockEmptyDbClient)
def test_initiate_config_error(*_args):
    """
    requirement: retrieve bugs from Cisco Service API per managedProduct configured
    mock: CiscoApiClient, db_client, cisco_authentication
    description: a config entry has to exist in the DB and the vendor has to be set to active by the user, when any of
                 these conditions are not met a ValueError(f"cisco vendor services are disabled") is raised and
                 "cisco vendor services are disabled" is returned in the message field
    :return:
    """
    # test a db operational error
    from vendor_cisco_bug_service import initiate
    assert initiate()["message"] == "cisco vendor services are disabled"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('vendor_cisco_api_client.CiscoApiClient')
@patch('db_client.Database', MockDbClientOperationalError)
def test_initiate_attribute_error(*_args):
    """
    requirement: retrieve bugs from Cisco Service API per managedProduct configured
    mock: CiscoApiClient, db_client, cisco_authentication
    description: simulate a database attribute error and ensure that it is being handled
    :return:
    """
    # test a db operational error
    from vendor_cisco_bug_service import initiate
    assert initiate()["message"] == "Database connection error - we are working on getting this fixed as soon " \
                                    "as possible"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('vendor_cisco_api_client.CiscoApiClient')
@patch('db_client.Database', MockDbClientSkipManagedProducts)
def test_initiate_no_managed_products_to_process(*_args):
    """
    requirement: retrieve bugs from Cisco Service API per managedProduct configured
    mock: CiscoApiClient, db_client, cisco_authentication
    description: simulate an execution where there are not managedProducts to process
    :return:
    """
    # test a db operational error
    from vendor_cisco_bug_service import initiate
    assert initiate()["message"] == "Database connection error - we are working on getting this fixed as soon " \
                                    "as possible"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                                   process_managed_product                                            #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_cisco_api_client.CiscoApiClient.bugs_by_prod_family_and_sv', lambda *_args, **_kwargs: [])
def test_process_managed_product_no_bugs_found(*_args):
    """
    requirement: check and process cisco bugs for a managed product and the sub products
    mock: CiscoApiClient, product_version_map, prod_family, cisco_api_client, bugs_date_back, support_token,
          bugs_table, db_client
    description: test a successful execution returning 0 bugs
    :return:
    """
    # test a db operational error
    from vendor_cisco_bug_service import process_managed_product
    from vendor_cisco_api_client import CiscoApiClient
    api_instance = CiscoApiClient(vendor_id="cisco")
    prod_family = type(
        "ProdFamily", (object,),
        {
            "name": "testProduct1", "lastExecution": datetime.datetime.strptime("2021-07-09", "%Y-%m-%d"),
            "vendorPriorities": [{"vendorPriority": "1"}], "id": 1, "vendorStatuses": ["O"]
        }
    )
    product_version_map = {"testProduct1": True}
    assert process_managed_product(
        prod_family=prod_family, cisco_api_client=api_instance, bugs_table="bugs", bugs_date_back=30,
        db_client=MockEmptyDbClient, support_token="", product_version_map=product_version_map
    )[0] == 0
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'vendor_cisco_api_client.CiscoApiClient.bugs_by_prod_family_and_sv',
    lambda *_args, **_kwargs: [{"bugId": 1, "managedProductId": 1}]
)
def test_process_managed_product_bug_key_error(*_args):
    """
    requirement: check and process cisco bugs for a managed product and the sub products
    mock: CiscoApiClient, product_version_map, prod_family, cisco_api_client, bugs_date_back, support_token,
          bugs_table, db_client
    description: simulate handling a keyError raised due to a wrong bug object schema
    :return:
    """
    # test a db operational error
    from vendor_cisco_bug_service import process_managed_product
    from vendor_cisco_api_client import CiscoApiClient
    api_instance = CiscoApiClient(vendor_id="cisco")
    prod_family = type(
        "ProdFamily", (object,),
        {
            "name": "testProduct1", "lastExecution": datetime.datetime.strptime("2021-07-09", "%Y-%m-%d"),
            "vendorPriorities": [{"vendorPriority": "1"}], "id": 1, "vendorStatuses": ["O"]
        }
    )
    product_version_map = {"testProduct1": True}
    try:
        process_managed_product(
            prod_family=prod_family, cisco_api_client=api_instance, bugs_table="bugs", bugs_date_back=30,
            db_client=MockEmptyDbClient, support_token="", product_version_map=product_version_map
        )
        assert False
    except KeyError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'vendor_cisco_api_client.CiscoApiClient.bugs_by_prod_family_and_sv',
    lambda *_args, **_kwargs: [{"bugId": 1, "managedProductId": 1}]
)
def test_process_managed_product_operational_error(*_args):
    """
    requirement: check and process cisco bugs for a managed product and the sub products
    mock: CiscoApiClient, product_version_map, prod_family, cisco_api_client, bugs_date_back, support_token,
          bugs_table, db_client
    description: simulate handling a database operational error
    :return:
    """
    # test a db operational error
    from vendor_cisco_bug_service import process_managed_product
    from vendor_cisco_api_client import CiscoApiClient
    api_instance = CiscoApiClient(vendor_id="cisco")
    prod_family = type(
        "ProdFamily", (object,),
        {
            "name": "testProduct1", "lastExecution": datetime.datetime.strptime("2021-07-09", "%Y-%m-%d"),
            "vendorPriorities": [{"vendorPriority": "1"}], "id": 1, "vendorStatuses": ["O"]
        }
    )
    product_version_map = {"testProduct1": True}
    try:
        process_managed_product(
            prod_family=prod_family, cisco_api_client=api_instance, bugs_table="bugs", bugs_date_back=30,
            db_client=MockDbClientNoExistingBugs, support_token="", product_version_map=product_version_map
        )
        assert False
    except OperationalError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


########################################################################################################################
#                                                   cisco_authentication                                               #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
def test_cisco_authentication_success(*_args):
    """
    requirement: follow cisco authentication flow to retrieve cisco_customer_id, support_token, service_token used to
                 consume the cisco service and supports APIs
    mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_cisco_bug_service import cisco_authentication
    api_instance = type("mockApiClient", (object,),
                        {"generate_service_api_token": lambda *_args, **_kwargs: [True, True],
                         "generate_support_api_tokens": lambda *_args, **_kwargs: [True, True],
                         "get_oath_cred": lambda *_args, **_kwargs: {"ClientId": "", "ClientSecret": ""},
                         "get_service_api_customer_id": lambda *_args, **_kwargs: "test",
                         }
                        )
    assert cisco_authentication(
        cisco_config={"serviceSecretId": "", "supportSecretId": ""}, cisco_api_client=api_instance
    )[0] == "test"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
def test_cisco_authentication_connection_error(*_args):
    """
    requirement: follow cisco authentication flow to retrieve cisco_customer_id, support_token, service_token used to
                 consume the cisco service and supports APIs
    mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
    description: test a failed request due to api connection that results in a connectionError being raised
    :return:
    """
    from vendor_cisco_bug_service import cisco_authentication
    api_instance = type("mockApiClient", (object,),
                        {"generate_service_api_token": lambda *_args, **_kwargs: mock_connection_error(),
                         "generate_support_api_tokens": lambda *_args, **_kwargs: [True, True],
                         "get_oath_cred": lambda *_args, **_kwargs: {"ClientId": "", "ClientSecret": ""},
                         "get_service_api_customer_id": lambda *_args, **_kwargs: "test",
                         }
                        )
    try:
        cisco_authentication(
            cisco_config={"serviceSecretId": "", "supportSecretId": ""}, cisco_api_client=api_instance
        )
    except ConnectionError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
def test_cisco_authentication_credentials_error(*_args):
    """
    requirement: follow cisco authentication flow to retrieve cisco_customer_id, support_token, service_token used to
                 consume the cisco service and supports APIs
    mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
    description: test a failed request due to api connection that results in a NameError being raised
    :return:
    """
    from vendor_cisco_bug_service import cisco_authentication
    api_instance = type("mockApiClient", (object,),
                        {"generate_service_api_token": lambda *_args, **_kwargs: mock_connect_name_error(),
                         "generate_support_api_tokens": lambda *_args, **_kwargs: [True, True],
                         "get_oath_cred": lambda *_args, **_kwargs: {"ClientId": "", "ClientSecret": ""},
                         "get_service_api_customer_id": lambda *_args, **_kwargs: "test",
                         }
                        )
    try:
        cisco_authentication(
            cisco_config={"serviceSecretId": "", "supportSecretId": ""}, cisco_api_client=api_instance
        )
    except NameError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_bug_service']
    del sys.modules['vendor_cisco_api_client']


# @patch.dict(os.environ, mock_env())
# @patch('db_client.Database')
# @patch('vendor_cisco_api_client.CiscoApiClient.generate_service_api_token', mock_connect_name_error)
# def test_initiate_credentials_error(*_args):
#     """
#         requirement: use credentials from context to test the the cisco auth method and return a status
#     mock: CiscoApiClient, generate_support_api_tokens, generate_service_api_token
#     description: test a failed request due to api bad credentials returning
#                  "authentication failed - check Cisco Service API Client Id / Client Secret"
#     :param _args:
#     :return:
#     """
#     from vendor_cisco_test_credentials import initiate
#     assert initiate(
#         mock_bad_credentials_verification_event
#     )["message"] == "authentication failed - check Cisco Service API Client Id / Client Secret"
#     # remove mocks import to prevent interference with other tests
#     del sys.modules['db_client']
#     del sys.modules['vendor_cisco_test_credentials']

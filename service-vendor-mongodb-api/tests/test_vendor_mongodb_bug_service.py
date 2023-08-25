"""
unit test fro vendor_mongodb_bug_service
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import MockEmptyDbClient, mock_env, mock_connection_error, \
    mock_operational_error, mock_managed_products_query_result, mock_managed_products_query_result_no_version


########################################################################################################################
#                                                   initiate TESTS                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_mongodb_api_client.MongoApiClient.prepare_managed_products', mock_operational_error)
@patch('db_client.Database')
def test_initiate_operation_error(*_args):
    """
    initiate class forcing db operational error and catching the exception
    :return:
    """
    # test a db operational error
    from vendor_mongodb_bug_service import initiate
    assert initiate()["message"] == "Database connection error - we are working on getting this fixed as soon as " \
                                    "we can"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_bug_service']


@patch.dict(os.environ, mock_env())
@patch('vendor_mongodb_api_client.MongoApiClient')
@patch('db_client.Database', MockEmptyDbClient)
def test_initiate_no_config(*_args):
    """
    test catching an exception for missing configuration file for tenant
    :return:
    """
    from vendor_mongodb_bug_service import initiate
    assert initiate()["message"] == f"mongodb vendor services are disabled or not configured"

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_bug_service']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch('vendor_mongodb_api_client.MongoApiClient.prepare_managed_products',
       mock_managed_products_query_result_no_version)
def test_initiate_managed_product_missing_versions(*_args):
    """
    - ManagedProducts should have at least one productSoftwareVersions entry to run the bug search
    - the separate sync service gets the version from serviceNow and thus has to run first to populate the version
    * test a managedProducts that has not versions and will rasie an EnvironmentError exception that has to be caught
    :return:
    """
    from vendor_mongodb_bug_service import initiate
    assert "no versions populated - Waiting for MongoDB Sync Service to" in initiate()["message"]

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_bug_service']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch('vendor_mongodb_api_client.MongoApiClient.prepare_managed_products',
       mock_managed_products_query_result)
@patch('vendor_mongodb_api_client.MongoApiClient.gen_search_filter_map')
@patch('vendor_mongodb_api_client.MongoApiClient.create_jql_query')
@patch('vendor_mongodb_api_client.MongoApiClient.get_bugs', mock_connection_error)
def test_initiate_get_bugs_connection_error(*_args):
    """
    test when mongodb_api_client.get_bugs returns a generic connection error message
    :return:
    """
    from vendor_mongodb_bug_service import initiate
    assert initiate()["message"] == "Vendor integration error - MongoDB data APIs are not working properly"

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_bug_service']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch('vendor_mongodb_api_client.MongoApiClient.prepare_managed_products', lambda *args, **kwargs: [])
def test_initiate_no_managed_products(*_args):
    """
    test the behaviour of the api when there are no managedProducts
    :return:
    """
    from vendor_mongodb_bug_service import initiate
    assert initiate()["message"] == f"there are no active products to process"

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_bug_service']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
@patch(
    'vendor_mongodb_api_client.MongoApiClient.prepare_managed_products', mock_managed_products_query_result
)
@patch('vendor_mongodb_api_client.MongoApiClient.gen_search_filter_map')
@patch('vendor_mongodb_api_client.MongoApiClient.create_jql_query')
@patch('vendor_mongodb_api_client.MongoApiClient.get_bugs')
@patch(
    'vendor_mongodb_api_client.MongoApiClient.insert_bug_updates',
    lambda *args, **kwargs: {"inserted_bugs": 0, "skipped_bugs": 0, "updated_bugs": 0}
)
def test_initiate(*_args):
    """
    simulate a successful execution returning stats message
    :return:
    """
    from vendor_mongodb_bug_service import initiate
    assert f"inserted_bugs" in initiate()["message"]

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_bug_service']

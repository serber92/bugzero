"""
unit test fro vendor_mongodb_sync_service
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import MockDbClientWithManagedProductsNoBugs, MockEmptyDbClient, mock_env


########################################################################################################################
#                                                   initiate TESTS                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_mongodb_api_client.MongoApiClient')
@patch('db_client.Database', MockEmptyDbClient)
def test_initiate_no_config(*_args):
    """
    test catching an exception for missing configuration file for tenant
    :return:
    """
    from vendor_mongodb_sync_service import initiate
    assert initiate()["message"] == f"mongodb vendor services are disabled or not configured"

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_sync_service']


@patch.dict(os.environ, mock_env())
@patch('vendor_mongodb_api_client.MongoApiClient')
@patch('db_client.Database', MockDbClientWithManagedProductsNoBugs)
def test_initiate_missing_service_now_config(*_args):
    """
    test when the db is missing the servicenow configuration file needed for the SN sync
    :return:
    """
    from vendor_mongodb_sync_service import initiate
    assert initiate()["message"] == f"ServiceNow connection info is missing - please check ServiceNow " \
                                    f"configurations page"

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_sync_service']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database')
def test_initiate(*_args):
    """
    simulate a successful execution returning empty
    :return:
    """
    from vendor_mongodb_sync_service import initiate
    assert initiate()["message"] == "managedProduct sn version count - []"

    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_mongodb_api_client']
    del sys.modules['vendor_mongodb_sync_service']

"""
unit tests for vendor_vmware_api_client
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, MockDbClientManagedProductsEmpty, MockEmptyDbClient


########################################################################################################################
#                                                   initiate                                                          #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_cisco_api_client.CiscoApiClient')
@patch('db_client.Database')
def test_initiate(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service API - update db if new products are found
    mock: CiscoApiClient, db_client
    description: a successful execution should result in a "Sync process completed successfully" message field value
    :return:
    """
    from vendor_cisco_sync_service import initiate
    assert initiate()["message"] == "Sync process completed successfully"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_api_client']
    del sys.modules['vendor_cisco_sync_service']


@patch.dict(os.environ, mock_env())
@patch('vendor_cisco_api_client.CiscoApiClient')
@patch('db_client.Database', MockEmptyDbClient)
def test_initiate_no_config(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service API - update db if new products are found
    mock: CiscoApiClient, db_client ( missing vendor config entry )
    description: test a simple initiate with missing config in the DB - catch exception that should result in
                 "cisco vendor services are disabled or not configured" message field value
    :return:
    """
    from vendor_cisco_sync_service import initiate
    assert initiate()["message"] == f"cisco vendor services are disabled or not configured"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_api_client']
    del sys.modules['vendor_cisco_sync_service']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database', MockDbClientManagedProductsEmpty)
@patch(
    'vendor_cisco_api_client.CiscoApiClient.get_hardware_inventory',
    lambda *_args, **_kwargs: [{"productFamily": "testProduct3", "productType": "Routers"}]
)
@patch(
    'vendor_cisco_api_client.CiscoApiClient.get_oath_cred',
    lambda *_args, **_kwargs: {"ClientId": "", "ClientSecret": ""}
)
@patch(
    'vendor_cisco_api_client.CiscoApiClient.get_service_api_customer_id',
    lambda *_args, **_kwargs: {"customerId": ""}
)
@patch(
    'vendor_cisco_api_client.CiscoApiClient.generate_service_api_token',
    lambda *_args, **_kwargs: True
)
@patch('vendor_cisco_api_client.CiscoApiClient.get_oath_cred', lambda *_args, **_kwargs: True)
def test_initiate_key_error(*_args):
    """
    requirement: retrieve hardware inventory from cisco-service API - update db if new products are found
    mock: CiscoApiClient, db_client ( missing vendor config entry )
    description: test a simple initiate with index error resulting of miss configured config entry -
                 catch exception that should result in
                 "cisco vendor services are disabled or not configured" message field value
    :return:
    """
    from vendor_cisco_sync_service import initiate
    assert initiate()["message"] == "Database configuration error - we are working on getting this fixed as soon as " \
                                    "possible"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_cisco_api_client']
    del sys.modules['vendor_cisco_sync_service']

"""
unit tests for vendor_vmware_sync_service.py
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, MockEmptyDbClient, mock_vmware_config, mock_db_client, \
    mock_managed_products, mock_vmware_api_client, mock_skyline_inventory, mock_other_managed_products


########################################################################################################################
#                                                   initiate TESTS                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_vmware_sync_service.get_inventory', lambda **_kwargs: True)
@patch('vendor_vmware_sync_service.get_auth', lambda **_kwargs: [True, True])
@patch('vendor_vmware_api_client.VmwareApiClient')
@patch('db_client.Database')
def test_initiate(*_args):
    """
    test a simple initiate and evaluate to True
    :return:
    """
    from vendor_vmware_sync_service import initiate
    assert initiate() is True
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_vmware_api_client']
    del sys.modules['vendor_vmware_sync_service']


@patch.dict(os.environ, mock_env())
@patch('vendor_vmware_sync_service.get_inventory', lambda **_kwargs: True)
@patch('vendor_vmware_sync_service.get_auth', lambda **_kwargs: [True, True])
@patch('vendor_vmware_api_client.VmwareApiClient')
@patch('db_client.Database', MockEmptyDbClient)
def test_initiate_no_config(*_args):
    """
    test a simple initiate with missing config in the DB - catch exception
    :return:
    """
    from vendor_vmware_sync_service import initiate
    assert initiate()["message"] == f"vmware vendor services are disabled or not configured"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_vmware_api_client']
    del sys.modules['vendor_vmware_sync_service']


########################################################################################################################
#                                                   get_auth TESTS                                                     #
########################################################################################################################
def test_get_auth_empty_config():
    """
    test an empty config files return from database and should raise an exception
    :return:
    """
    from vendor_vmware_sync_service import get_auth
    # setting vmware_config to {}
    vmware_config = mock_vmware_config(config_example={})
    client_class = type('VmwareApiClient', (object,), {'bug_zero_vendor_status_update': "vmware"})
    api_client = mock_vmware_api_client(client_class)
    vendor_id = "vmware"
    try:
        get_auth(vmware_config=vmware_config, vendor_id=vendor_id, vmware_api_client=api_client)
        assert True
    except ValueError:
        assert True


def test_get_auth_empty_secret_id():
    """
    test a config files return from database w empty secretId field should raise an exception
    :return:
    """
    from vendor_vmware_sync_service import get_auth
    client_class = type('VmwareApiClient', (object,), {'vendor_id': "vmware"})
    api_client = mock_vmware_api_client(client_class)
    # setting secretId to false
    vmware_config = mock_vmware_config(config_example={"secretId": False})
    vendor_id = "vmware"
    try:
        get_auth(vmware_config=vmware_config, vendor_id=vendor_id, vmware_api_client=api_client)
        assert False
    except ValueError:
        assert True


def test_get_auth_no_tokens():
    """
    test an execution where the vmware login failed and returned no tokens
    :return:
    """
    from vendor_vmware_sync_service import get_auth
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            # setting tokens to false
            "get_auth_token": lambda **_kwargs: False,
        }
    )
    api_client = mock_vmware_api_client(client_class)
    vmware_config = mock_vmware_config(config_example={"secretId": True})
    vendor_id = "vmware"
    try:
        get_auth(vmware_config=vmware_config, vendor_id=vendor_id, vmware_api_client=api_client)
        assert False
    except ValueError:
        assert True


def test_get_auth_w_tokens():
    """
    test a successful execution that returned tokens
    :return:
    """
    from vendor_vmware_sync_service import get_auth
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            # setting tokens to true
            "get_auth_token": lambda **_kwargs: True,
        }
    )
    api_client = mock_vmware_api_client(client_class)
    vmware_config = mock_vmware_config(config_example={"secretId": True})
    vendor_id = "vmware"
    try:
        get_auth(vmware_config=vmware_config, vendor_id=vendor_id, vmware_api_client=api_client)
        assert True
    except ValueError:
        assert False


#######################################################################################################################
#                                                  get_inventory TESTS                                                #
#######################################################################################################################
def test_get_inventory_non_healthy_collectors():
    """
    test an execution where the collector is not healthy and an exception should be raised
    :return:
    """
    from vendor_vmware_sync_service import get_inventory
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            "get_auth_token": lambda **_kwargs: True,
            # setting health to false
            "check_collectors_health": lambda **_kwargs: False
        }
    )
    api_client = mock_vmware_api_client(client_class)
    # setting default kwargs
    kw_args = {
        "vmware_service_cred": "", "managed_products": "", "tokens": [True, True],
        "managed_products_table": "", "vmware_config": "", "db_client": "", "vendor_id": ""
    }
    try:
        get_inventory(vmware_api_client=api_client, **kw_args)
        assert False
    except ValueError:
        assert True


def test_get_inventory_non_inventory():
    """
    test an execution where the collector inventory is empty
    :return:
    """
    from vendor_vmware_sync_service import get_inventory
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            "get_auth_token": lambda **_kwargs: True,
            # setting health to True
            "check_collectors_health": lambda **_kwargs: True,
            # mock inventory
            "get_inventory": lambda **_kwargs: False,

        }
    )
    api_client = mock_vmware_api_client(client_class)
    # setting default kwargs
    kw_args = {
        "vmware_service_cred": {"orgId": True}, "managed_products": "", "tokens": [True, True],
        "managed_products_table": "", "vmware_config": "", "db_client": "", "vendor_id": ""
    }
    try:
        get_inventory(vmware_api_client=api_client, **kw_args)
        assert False
    except ValueError:
        assert True


def test_get_inventory_existing_managed_products():
    """
    test an execution where all managedProduct exist
    :return:
    """
    from vendor_vmware_sync_service import get_inventory
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            "get_auth_token": lambda **_kwargs: True,
            # setting health to True
            "check_collectors_health": lambda **_kwargs: True,
            # mock inventory
            "get_inventory": lambda **_kwargs: mock_skyline_inventory(),

        }
    )
    api_client = mock_vmware_api_client(client_class)
    # setting default kwargs
    # managed_products has non-relevant products
    kw_args = {
        "vmware_service_cred": {"orgId": True}, "managed_products": mock_managed_products(), "tokens": [True, True],
        "managed_products_table": "", "vmware_config": "", "db_client": mock_db_client(), "vendor_id": ""
    }
    assert get_inventory(vmware_api_client=api_client, **kw_args)["message"] == f"0 managed product(s) inserted"


def test_get_inventory_new_managed_products():
    """
    test an execution where all managedProduct exist
    :return:
    """
    from vendor_vmware_sync_service import get_inventory
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            "get_auth_token": lambda **_kwargs: True,
            # setting health to True
            "check_collectors_health": lambda **_kwargs: True,
            # mock inventory
            "get_inventory": lambda **_kwargs: mock_skyline_inventory(),

        }
    )
    vmware_config = mock_vmware_config(
        {"vendorPriorities": "", "vendorStatuses": ""}
    )
    api_client = mock_vmware_api_client(client_class)
    # setting default kwargs
    # managed_products has non-relevant products
    kw_args = {
        "vmware_service_cred": {"orgId": True}, "managed_products": mock_other_managed_products(),
        "tokens": [True, True], "managed_products_table": "test", "db_client": mock_db_client(), "vendor_id": "",
        "vmware_config": vmware_config
    }
    assert get_inventory(vmware_api_client=api_client, **kw_args)["message"] == f"2 managed product(s) inserted"

"""
unit test fro vendor_vmware_bug_service
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error, MockEmptyDbClient, mock_vmware_config, \
    mock_vmware_api_client, MockDbClientManagedProductsEmpty, MockDbClientWithManagedProductsNoBugs, \
    mock_skyline_inventory, mock_product_by_morid_no_bugs, mock_product_by_morid_1_bug, \
    MockDbClientWithManagedProductsWithExistingOldBug, MockDbClientWithManagedProductsWithExistingSimilarBug


########################################################################################################################
#                                                   initiate TESTS                                                     #
########################################################################################################################

@patch.dict(os.environ, mock_env())
@patch('vendor_vmware_bug_service.process_managed_products', mock_operational_error)
@patch('vendor_vmware_api_client.VmwareApiClient')
@patch('db_client.Database')
def test_initiate_operation_error(*_args):
    """
    initiate class forcing db operational error and catching the exception
    :return:
    """
    # test a db operational error
    from vendor_vmware_bug_service import initiate
    assert initiate() == "Database connection error - we are working on getting this fixed as soon as we can"
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_vmware_api_client']
    del sys.modules['vendor_vmware_bug_service']


@patch.dict(os.environ, mock_env())
@patch('vendor_vmware_bug_service.process_managed_products', lambda **_kwargs: {"total_inserted_bugs": 5})
@patch('vendor_vmware_api_client.VmwareApiClient')
@patch('db_client.Database')
def test_initiate(*_args):
    """
    # test the function where the bug process returns 5 bugs
    :return:
    """
    from vendor_vmware_bug_service import initiate
    assert initiate()["total_inserted_bugs"] == 5
    # remove mocks import to prevent interference with other tests
    del sys.modules['db_client']
    del sys.modules['vendor_vmware_api_client']
    del sys.modules['vendor_vmware_bug_service']


@patch.dict(os.environ, mock_env())
@patch('vendor_vmware_bug_service.process_managed_products', lambda **_kwargs: {"total_inserted_bugs": 0})
@patch('vendor_vmware_api_client.VmwareApiClient')
@patch('db_client.Database', MockEmptyDbClient)
def test_initiate_no_config(*_args):
    """
    test catching an exception for missing configuration file for tenant
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
    from vendor_vmware_bug_service import get_auth
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
    from vendor_vmware_bug_service import get_auth
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
    from vendor_vmware_bug_service import get_auth
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
    from vendor_vmware_bug_service import get_auth
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
#                                             process_managed_products  TESTS                                         #
#######################################################################################################################
def test_process_managed_products_empty(*_args):
    """
    test an execution with no managed products to process that
    :return:
    """
    from vendor_vmware_bug_service import process_managed_products
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
    last_executed_gap = -1
    vmware_config = mock_vmware_config(config_example={"secretId": True})
    assert process_managed_products(
        db_client=MockDbClientManagedProductsEmpty,
        bugs_table="test", managed_products_table="managedProducts",
        vendor_id="vmware", vmware_api_client=client_class, vmware_config=vmware_config,
        last_executed_gap=last_executed_gap
    ) == "currently there are no products to process"


@patch('vendor_vmware_bug_service.get_auth')
def test_process_managed_products_2_products_no_inventory(get_auth):
    """
    DB: has 2 managed products
    Inventory: None
    test an execution with 2 managed products to process but no inventory
    :return:
    """
    from vendor_vmware_bug_service import process_managed_products

    # mock get auth
    get_auth.return_value = ({"orgId": True}, [True, True])
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            "get_auth_token": lambda **_kwargs: True,
            "check_collectors_health": lambda **_kwargs: True,
            "get_inventory": lambda **_kwargs: False,
        }
    )
    last_executed_gap = -1
    vmware_config = mock_vmware_config(config_example={"secretId": True})
    try:
        process_managed_products(
            db_client=MockDbClientWithManagedProductsNoBugs,
            bugs_table="test", managed_products_table="managedProducts",
            vendor_id="vmware", vmware_api_client=client_class, vmware_config=vmware_config,
            last_executed_gap=last_executed_gap)

        assert False
    except ValueError as e:
        if str(e) == "vmware skyline inventory is empty - check collectors":
            assert True
        else:
            assert False


@patch('vendor_vmware_bug_service.get_auth')
def test_process_managed_products_2_products_w_inventory(get_auth):
    """
    DB: has 2 managed products
    Inventory: has 2 products
    :return:
    """
    from vendor_vmware_bug_service import process_managed_products

    # mock get auth
    get_auth.return_value = ({"orgId": True}, [True, True])
    client_class = type(
        'VmwareApiClient', (object,),
        {
            'vendor_id': "vmware",
            "get_oath_cred": lambda **_kwargs: {"password": "test", "username": "test", "orgId": "test"},
            "get_auth_token": lambda **_kwargs: True,
            "check_collectors_health": lambda **_kwargs: True,
            "get_inventory": lambda **_kwargs: mock_skyline_inventory(),

        }
    )
    last_executed_gap = -1
    vmware_config = mock_vmware_config(config_example={"secretId": True})
    assert process_managed_products(
        db_client=MockDbClientWithManagedProductsNoBugs,
        bugs_table="test", managed_products_table="managedProducts",
        vendor_id="vmware", vmware_api_client=client_class, vmware_config=vmware_config,
        last_executed_gap=last_executed_gap) == f"0 new bugs published"


########################################################################################################################
#                                        process_managed_products TESTS                                               #
########################################################################################################################
def test_get_vmware_bugs_no_managed_products(*_args):
    """
    DB: no managed products
    test an execution with no managed products to process ( 0 bugs )
    :return:
    """
    from vendor_vmware_bug_service import get_vmware_bugs
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
    assert get_vmware_bugs(
        db_client=MockDbClientManagedProductsEmpty,
        bugs_table="test", tokens=[True, True], vmware_service_cred={"orgId": True},
        vmware_api_client=client_class, product_by_morid=mock_product_by_morid_no_bugs
    ) == f"0 new bugs published"


def test_get_vmware_bugs_1_bug(*_args):
    """
    test an execution with with managedProducts and 1 bug to insert to the db
    DB: has 2 managed products
    DB: has 0 bugs
    BUGS: 1 new bugs to insert

    :return:
    """
    from vendor_vmware_bug_service import get_vmware_bugs
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
    assert get_vmware_bugs(
        db_client=MockDbClientWithManagedProductsNoBugs,
        bugs_table="bugs_table", tokens=[True, True], vmware_service_cred={"orgId": True},
        vmware_api_client=client_class, product_by_morid=mock_product_by_morid_1_bug
    ) == f"1 new bugs published"


def test_get_vmware_bugs_1_existing_bug_update(*_args):
    """
    test an execution with with managedProducts and 1 bug to update in the db
    DB: has 2 managed products
    DB: has 1 bugs
    BUGS: a bug update for the db bug

    :return:
    """
    from vendor_vmware_bug_service import get_vmware_bugs
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
    assert get_vmware_bugs(
        db_client=MockDbClientWithManagedProductsWithExistingOldBug,
        bugs_table="bugs_table", tokens=[True, True], vmware_service_cred={"orgId": True},
        vmware_api_client=client_class, product_by_morid=mock_product_by_morid_1_bug
    ) == f"0 new bugs published"


def test_get_vmware_bugs_skipping_existing_similar_bug(*_args):
    """
    test an execution with with managedProducts and 1 bug to be skipped
    DB: has 2 managed products
    DB: has 1 bugs
    BUGS: a bug that already exist in DB

    :return:
    """
    from vendor_vmware_bug_service import get_vmware_bugs
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
    assert get_vmware_bugs(
        db_client=MockDbClientWithManagedProductsWithExistingSimilarBug,
        bugs_table="bugs_table", tokens=[True, True], vmware_service_cred={"orgId": True},
        vmware_api_client=client_class, product_by_morid=mock_product_by_morid_1_bug
    ) == f"0 new bugs published"

"""
unit testing for vendor_rh_bug_service
"""
import os
import sys
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error


########################################################################################################################
#                                                   initiate                                                          #
########################################################################################################################

@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: mock_operational_error())
@patch('db_client.Database.get_vendor_config', lambda **kwargs: mock_operational_error())
@patch('vendor_rh_api_client.RedHatApiClient.sn_sync')
@patch('vendor_rh_api_client.RedHatApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_operation_error(*_args):
    """
    requirement: the initiate function has many SqlAlchemy operations - db connection errors most be caught
    mock: db_client to return OperationalError
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_rh_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'OperationalError' in execution_message["message"]['errorType']
    # remove mocks import to prevent interference with other tests


@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor_config', lambda *args, **kwargs: False)
@patch('vendor_rh_api_client.RedHatApiClient.sn_sync')
@patch('vendor_rh_api_client.RedHatApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_vendor_config_missing(*_args):
    """
    requirement: the initiate function utilizes db_client.get_vendor_config to retrieve vendor config from the db
                 the entry for the vendor might be missing if the tenant user did not set the vendor in the bugZero
                 UI
    mock: db_client to return missing vendor config file
    description: the execution should result with an operational error ServiceNotConfigured
    :return:
    """
    from vendor_rh_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']


@patch.dict(os.environ, mock_env())
@patch('vendor_rh_api_client.RedHatApiClient.sn_sync')
@patch('vendor_rh_api_client.RedHatApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor_config', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor_status', lambda *args, **kwargs: False)
@patch('boto3.client')
def test_initiate_vendor_vendor_disabled(*_args):
    """
    requirement: the initiate function ensures that tha vendor is enabled in the DB and raises a VendorDisabled
                 exception when necessary

    mock: db_client to return disabled vendorEntry
    description: the execution should result with an operational error VendorDisabled
    :return:
    """
    from vendor_rh_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'VendorDisabled' in execution_message["message"]['errorType']


@patch.dict(os.environ, mock_env())
@patch('vendor_rh_api_client.RedHatApiClient.sn_sync')
@patch('vendor_rh_api_client.RedHatApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_vendor_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": None, "snAuthToken": None}})
)
@patch('db_client.Database.get_vendor_status', lambda *args, **kwargs: True)
@patch('boto3.client')
def test_initiate_missing_sn_config_variables(*_args):
    """
    requirement: SN variables from the SN service entry in the DB are necessary to run the sync process accessed by the
                 the initiate function - if those are empty a ServiceNotConfigured should be raised
    mock: db_client to return disabled vendorEntry
    description: the execution should result with an ServiceNotConfigured error
    :return:
    """
    from vendor_rh_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']


@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor_config')
@patch('db_client.Database.get_vendor_status', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: [])
@patch('vendor_rh_api_client.RedHatApiClient.sn_sync', lambda *args, **kwargs: {})
@patch('vendor_rh_api_client.RedHatApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_sync_empty(*_args):
    """
    requirement: bugs are retrieved when existing managedProducts or supportedProducts have consist of software version
                 found in the SN sync if
    mock: db_client to return one managed product, vendor_rh_api_client sn_sync and bug_zero_vendor_status_update
    description: the sync will return empty and thus the bug service will not start an a
                'no active SN CIs matching enabled managed products were found' will be returned and sent to the
                dashboard
    :return:
    """
    from vendor_rh_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"] == 'no active SN CIs matching enabled managed products were found'
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_rh_api_client']

"""
unit testing for vendor_fortinet_bug_service
"""
import os
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error, mock_sn_ci_query_response_json, \
    mock_disabled_managed_product, mock_just_processed_managed_product, \
    mock_sn_ci_query_response_json_missing_description_field, mock_sn_ci_query_response_json_empty_description_field, \
    mock_sn_ci_query_response_json_empty_hardware_os_field, mock_sn_ci_query_response_json_missing_hardware_os_field, \
    mock_managed_product, mock_sn_ci_query_response_json_w_2_cis, mock_database_init


########################################################################################################################
#                                                   initiate                                                          #
########################################################################################################################

@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: mock_operational_error())
@patch('db_client.Database.get_service_config', lambda **kwargs: mock_operational_error())
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_operation_error(*_args):
    """
    requirement: the initiate function has many SqlAlchemy operations - db connection errors most be caught
    mock: db_client to return OperationalError
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'OperationalError' in execution_message["message"]['errorType']
    # remove mocks import to prevent interference with other tests
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_service_config', lambda *args, **kwargs: False)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_vendor_config_missing(*_args):
    """
    requirement: the initiate function utilizes db_client.get_service_config to retrieve vendor config from the db
                 the entry for the vendor might be missing if the tenant user did not set the vendor in the bugZero
                 UI
    mock: db_client to return missing vendor config file
    description: the execution should result with an operational error ServiceNotConfigured
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_service_config', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: False)
@patch('boto3.client')
def test_initiate_vendor_disabled(*_args):
    """
    requirement: the initiate function ensures that tha vendor is enabled in the DB and raises a VendorDisabled
                 exception when necessary

    mock: db_client to return disabled vendorEntry
    description: the execution should result with an operational error VendorDisabled
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'VendorDisabled' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": None, "snAuthToken": None}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('boto3.client')
def test_initiate_missing_sn_config_variables(*_args):
    """
    requirement: SN variables from the SN service entry in the DB are necessary to run the sync process accessed by the
                 the initiate function - if those are empty a ServiceNotConfigured should be raised
    mock: db_client to return disabled vendorEntry
    description: the execution should result with an ServiceNotConfigured error
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_disabled_managed_product)
@patch('vendor_fortinet_api_client.FortinetApiClient.sn_sync', lambda *args, **kwargs: mock_sn_ci_query_response_json)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_disabled_managed_product(*_args):
    """
    requirement: if the sync service returns a product that exist as a managedProduct and that managedProduct is
                 disabled the managedProduct is skipped
    mock: disabled managedProduct, vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: the sync will return a product that exist as a disabled managedProduct and thus the bug service
                 will not start
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"] == '0 new bugs published'
    # remove mocks import to prevent interference with other tests
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch('vendor_fortinet_api_client.FortinetApiClient.sn_sync', lambda *args, **kwargs: mock_sn_ci_query_response_json)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_processed_managed_product(*_args):
    """
    requirement: if the sync service returns a product that exist as a managedProduct and that managedProduct has been
                 processed in the last 6 hours bug discovery won't run for the managedProduct
    mock: disabled managedProduct, vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: the sync will return a product that exist as a recently processed managedProduct and thus the bug
                 service will not start
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"] == '0 new bugs published'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_json_empty_description_field
)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_ci_product_name_error(*_args):
    """
    requirement: the Ci product name is parsed out from the 'short_description' field using regex
    mock: vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: ApiRegexParseError raised when failed to match product name regex
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"]["errorType"] == '<class \'vendor_exceptions.ApiRegexParseError\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_json_missing_description_field
)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_ci_missing_mandatory_field(*_args):
    """
    requirement: the Ci product name is parsed out from the 'short_description' field using regex
    mock: vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: SnCiFieldMissing raised when 'short_description' field is missing
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"]["errorType"] == '<class \'vendor_exceptions.SnCiFieldMissing\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_json_empty_hardware_os_field
)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_ci_os_version_error(*_args):
    """
    requirement: the Ci os version is parsed out from the 'hardware_os_version' field using regex
    mock: vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: ApiRegexParseError raised when failed to match os_version regex
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"]["errorType"] == '<class \'vendor_exceptions.ApiRegexParseError\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_json_missing_hardware_os_field
)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_ci_missing_version_field(*_args):
    """
    requirement: the Ci os version is parsed out from the 'hardware_os_version' field using regex
    mock: vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: SnCiFieldMissing raised when 'hardware_os_version' field is missing
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"]["errorType"] == '<class \'vendor_exceptions.SnCiFieldMissing\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.update_managed_product_versions', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_managed_product)
@patch(
    'db_client.Database.insert_bug_updates',
    lambda *args, **kwargs: {"updated_bugs": 0, "inserted_bugs": 1, "skipped_bugs": 0}
)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_json_w_2_cis
)
@patch('vendor_fortinet_api_client.FortinetApiClient.bug_zero_vendor_status_update')
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.generate_release_notes_urls',
    lambda *_args, **_kwargs: [{"url": "", "version": ""}]
)
@patch('vendor_fortinet_api_client.FortinetApiClient.get_bugs', lambda *_args, **_kwargs: ["test"])
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.consolidate_bugs',
    lambda *_args, **_kwargs: [{"knownAffectedReleases": ["7.0.1"]}]
)
@patch(
    'vendor_fortinet_api_client.FortinetApiClient.format_bug_entry',
    lambda *_args, **_kwargs: [{"knownAffectedReleases": ["7.0.1"]}]
)
@patch('boto3.client')
def test_initiate_ci_successful(*_args):
    """
    requirement: insert bugs found per managedProduct, auto-added / auto-updated by sn sync
    mock: vendor_fortinet_api_client.sn_sync and bug_zero_vendor_status_update
    description: 1 new bug inserted
    :return:
    """
    from vendor_fortinet_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-rh-bug-service",
                                        "log_group_name": "dev-vendor-rh-bug-service"}
             )
    )
    assert execution_message["message"] == '1 new bugs published'

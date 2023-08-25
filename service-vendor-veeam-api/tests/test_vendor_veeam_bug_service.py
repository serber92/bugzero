"""
unit testing for vendor_veeam_bug_service
"""
import os
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error, \
    mock_disabled_managed_product, mock_just_processed_managed_product, mock_sn_ci_query_response_json, \
    mock_sn_ci_query_response_json_empty, mock_database_init, mock_managed_product, mock_sn_ci_query_response_no_version


########################################################################################################################
#                                                   initiate                                                           #
########################################################################################################################

@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: mock_operational_error())
@patch('db_client.Database.get_service_config', lambda **kwargs: mock_operational_error())
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_operation_error(*_args):
    """
    requirement: the initiate function has many SqlAlchemy operations - db connection errors most be caught
    mock: db_client to return OperationalError
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
             )
    )
    assert 'OperationalError' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_service_config', lambda *args, **kwargs: False)
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
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
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_service_config', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: False)
@patch('boto3.client')
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
def test_initiate_vendor_disabled(*_args):
    """
    requirement: the initiate function ensures that tha vendor is enabled in the DB and raises a VendorDisabled
                 exception when necessary

    mock: db_client to return disabled vendorEntry
    description: the execution should result with an operational error VendorDisabled
    :return:
    """
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
             )
    )
    assert 'VendorDisabled' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
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
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
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
@patch(
    'vendor_veeam_api_client.VeeamApiClient.crawl_vendor_products',
    lambda *args, **kwargs: [{
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }]
)
@patch('vendor_veeam_api_client.VeeamApiClient.sn_sync', lambda *args, **kwargs: mock_sn_ci_query_response_json_empty)
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_sn_no_cis(*_args):
    """
    requirement: sn sync return 0 CI entries
    mock: managedProduct, vendor_veeam_bug_service.sn_sync and bug_zero_vendor_status_update, sn query response
    description: the sync will return a message stating that 0 CI were found for enabled manated products
    :return:
    """
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
             )
    )
    assert execution_message["message"] == 'no active SN CIs matching enabled managed products were found'
    # remove mocks import to prevent interference with other tests
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,),
                                 {"value": {"daysBack": 120, "snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch('vendor_veeam_api_client.VeeamApiClient.sn_sync', lambda *args, **kwargs: mock_sn_ci_query_response_json)
@patch(
    'vendor_veeam_api_client.VeeamApiClient.crawl_vendor_products',
    lambda *args, **kwargs: [{
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }]
)
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_processed_managed_product(*_args):
    """
    requirement: if the sync service returns a product that exist as a managedProduct and that managedProduct has been
                 processed in the last 6 hours bug discovery won't run for the managedProduct
    mock: disabled managedProduct, vendor_veeam_api_client.sn_sync and bug_zero_vendor_status_update
    description: the sync will return a product that exist as a recently processed managedProduct and thus the bug
                 service will not start
    :return:
    """
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
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
@patch(
    'vendor_veeam_api_client.VeeamApiClient.crawl_vendor_products',
    lambda *args, **kwargs: [{
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }]
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: True)
@patch(
    'vendor_veeam_api_client.VeeamApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_no_version
)
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_ci_product_missing_version_field(*_args):
    """
    requirement: the Ci version is taken out from the 'version' field and is necessary for finding bugs
    mock: vendor_veeam_api_client.sn_sync and bug_zero_vendor_status_update
    description: SnCiFieldMissing raised when the version field is missing or empty
    :return:
    """
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
             )
    )
    assert execution_message["message"]["errorType"] == '<class \'vendor_exceptions.SnCiFieldMissing\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,),
                                 {"value": {"daysBack": 100, "snApiUrl": True, "snAuthToken": True}})
)
@patch(
    'vendor_veeam_api_client.VeeamApiClient.crawl_vendor_products',
    lambda *args, **kwargs: [{
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }]
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.update_managed_product_versions', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_managed_product)
@patch(
    'vendor_veeam_api_client.VeeamApiClient.sn_sync',
    lambda *args, **kwargs: mock_sn_ci_query_response_json
)
@patch('vendor_veeam_api_client.VeeamApiClient.bug_zero_vendor_status_update')
@patch('vendor_veeam_api_client.VeeamApiClient.get_kb_article_links', lambda *args, **kwargs: [])
@patch('vendor_veeam_api_client.VeeamApiClient.get_bugs', lambda *args, **kwargs: [])
@patch('boto3.client')
def test_initiate_no_bugs_found(*_args):
    """
    requirement: skip product if no bugs are found
    mock: vendor_veeam_api_client.sn_sync and bug_zero_vendor_status_update
    description: SnCiFieldMissing raised when the version field is missing or empty
    :return:
    """
    from vendor_veeam_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "test", "function_name": "dev-vendor-veeam-bug-service",
                                        "log_group_name": "dev-vendor-veeam-bug-service"}
             )
    )
    assert execution_message["message"] == '0 new bugs published'

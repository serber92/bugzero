"""
unit testing for vendor_msft_bug_service
"""
import datetime
import os
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error, mock_api_response_error, mock_database_init, \
    mock_disabled_managed_products, mock_to_execute_windows_server_managed_product, \
    mock_to_execute_sql_server_managed_product, mock_to_execute_access_server_managed_product


########################################################################################################################
#                                                    initiate                                                          #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: mock_operational_error())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_operation_error(*_args):
    """
    requirement: the initiate function has many SqlAlchemy operations - db connection errors most be caught
    mock: db_client to return OperationalError
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert 'OperationalError' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_settings', lambda *args, **kwargs: False)
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_service_config_missing(*_args):
    """
    requirement: the initiate function utilizes db_client.get_settings to retrieve service settings from the db.
                 the entry for the service settings might be missing if the tenant user did not configured the vendor in
                 the bugZero UI
    mock: db_client to return missing service settings entry
    description: the execution should result with an operational error ServiceNotConfigured
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message['message']['errorType'] == '<class \'vendor_exceptions.ServiceNotConfigured\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: False)
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_vendor_config_missing(*_args):
    """
    requirement: the initiate function utilizes db_client.get_vendor to retrieve vendor config from the db
                 the entry for the vendor might be missing if the tenant user did not set the vendor in the bugZero
                 UI
    mock: db_client to return missing vendor config entry
    description: the execution should result with an operational error VendorDisabled
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message['message']['errorType'] == '<class \'vendor_exceptions.VendorDisabled\'>'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": None, "snAuthToken": None}}
                                    ))
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('boto3.client')
def test_initiate_missing_sn_config_variables(*_args):
    """
    requirement: SN variables from the SN service entry in the DB are necessary to run the sync process accessed by the
                 the initiate function - if those are empty a ServiceNotConfigured should be raised
    mock: db_client to return empty sn_config entry
    description: the execution should result with an ServiceNotConfigured error
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs: mock_api_response_error())
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: False)
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products')
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch('boto3.client')
def test_admin_dashboard_response_error(*_args):
    """
    requirement: the windows server issues endpoint from the Admin Dashboard API might be unavailable,
                 an ApiResponseError should be raised to trigger an SN event but the service should continue and
                 process the remaining msft products
    mock: msft_api_client.get_windows_issues to return ApiResponseError
    description: the execution should complete without errors
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: 1)
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products')
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch('db_client.Database.create_managed_product',
       lambda *args, **kwargs: type("mockConfig", (object,), {"id": 999, "isDisabled": True, "name": "test"}))
@patch('boto3.client')
def test_all_managed_products_are_disabled(*_args):
    """
    requirement: process the msft supported products and complete the process as all the managedProducts are disabled
    mock: mock db_client to return disabled managedProducts
    description: the execution should complete without errors
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: 1)
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products')
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.create_managed_product',
    lambda *args, **kwargs: type(
        "mockConfig", (object,), {"id": 999, "isDisabled": 0, "name": "test",
                                  "lastExecution": datetime.datetime.now()})
)
@patch('boto3.client')
def test_all_managed_products_have_been_processed(*_args):
    """
    requirement: process the msft supported products and complete the process as all the managedProducts have been
                 recently processed
    mock: mock db_client to return recently processed managedProducts
    description: the execution should complete without errors
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: 1)
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_disabled_managed_products)
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch('db_client.Database.create_managed_product',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"id": 999, "isDisabled": 0, "name": "test", "lastExecution": datetime.datetime.now()})
       )
@patch('boto3.client')
def test_all_managed_products_exist_and_disabled(*_args):
    """
    requirement: all the msft supported products exist as disabled managedProducts
    mock: mock db_client to return disabled managedProduct for every supported msft product
    description: the execution should complete without errors
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.filter_product_issues')
@patch(
    'vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs:
    [{"KnownIssues": [1], "Version": "Windows Server 2022"}]
)
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: 1)
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.insert_bug_updates', lambda *args, **kwargs:
    {"updated_bugs": 0, "inserted_bugs": 1, "skipped_bugs": 0}
)
@patch('db_client.Database.get_managed_products',
       lambda *args, **kwargs: mock_to_execute_windows_server_managed_product
       )
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch('db_client.Database.create_managed_product',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"id": 999, "isDisabled": 0, "name": "test", "lastExecution": datetime.datetime.now()})
       )
@patch('boto3.client')
def test_windows_server_managed_products_not_executed(*_args):
    """
    requirement: all the msft supported products exist and only windows server products haven't been executed, will be
                 processed by the service, if bug founds, an sns message will trigger the bugEventProcessor
    mock: mock db_client to return microsoft server managedProducts that have not been executed, mock aws sns client
    description: the execution should complete without errors, simulate publishing an sns message to execute the
                 bugEventProcessor
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.filter_product_issues')
@patch('vendor_msft_api_client.MsftApiClient.get_sql_release_bugs', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.consolidate_bugs', lambda *args, **kwargs: [1])
@patch('vendor_msft_api_client.MsftApiClient.format_sql_bugs', lambda *args, **kwargs: [1])
@patch('vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: 1)
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.insert_bug_updates', lambda *args, **kwargs:
    {"updated_bugs": 0, "inserted_bugs": 1, "skipped_bugs": 0}
)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_to_execute_sql_server_managed_product)
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch('db_client.Database.create_managed_product',
       lambda *args, **kwargs: type("mockConfig", (object,),
                                    {"id": 999, "isDisabled": 0, "name": "test",
                                     "lastExecution": datetime.datetime.now()})
       )
@patch('boto3.client')
def test_sql_server_managed_products_not_executed(*_args):
    """
    requirement: all the msft supported products exist and only sql server products haven't been executed, will be
                 processed by the service, if bug founds, an sns message will trigger the bugEventProcessor
    mock: mock db_client to return sql server managedProducts that have not been executed, mock aws sns client
    description: the execution should complete without errors, simulate publishing an sns message to execute the
                 bugEventProcessor
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_zero_vendor_status_update')
@patch('vendor_msft_api_client.MsftApiClient.get_aws_secret_value')
@patch('vendor_msft_api_client.MsftApiClient.gen_admin_dashboard_tokens')
@patch('vendor_msft_api_client.MsftApiClient.filter_product_issues')
@patch('vendor_msft_api_client.MsftApiClient.get_access_bug_kbs', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.format_access_bugs', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.get_windows_issues', lambda *args, **kwargs: [])
@patch('vendor_msft_api_client.MsftApiClient.sn_sync', lambda *args, **kwargs: [{}])
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.insert_bug_updates',
    lambda *args, **kwargs: {"updated_bugs": 0, "inserted_bugs": 1, "skipped_bugs": 0}
)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_to_execute_access_server_managed_product)
@patch('db_client.Database.get_settings',
       lambda *args, **kwargs:
       type("mockConfig", (object,),
            {"value": {"snApiUrl": True, "snAuthToken": True, "secretId": True, "daysBack": 1}})
       )
@patch('db_client.Database.get_vendor', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: True)
@patch('db_client.Database.create_managed_product',
       lambda *args, **kwargs: type("mockConfig", (object,),
                                    {"id": 999, "isDisabled": 0, "name": "test",
                                     "lastExecution": datetime.datetime.now()})
       )
@patch('boto3.client')
def test_access_managed_products_not_executed(*_args):
    """
    requirement: all the msft supported products exist and only microsoft access products haven't been executed, will be
                 processed by the service, if bug founds, an sns message will trigger the bugEventProcessor
    mock: mock db_client to return microsoft access managedProducts that have not been executed, mock aws sns client
    description: the execution should complete without errors, simulate publishing an sns message to execute the
                 bugEventProcessor
    :return:
    """
    from vendor_msft_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "msft-bug-svc",
            "log_group_name": "msft-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
    assert execution_message["message"]

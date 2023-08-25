"""
unit testing for vendor_netapp_bug_service
"""
import os
import time
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error, mock_database_init, mock_managed_product


########################################################################################################################
#                                                   initiate                                                           #
########################################################################################################################

@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: mock_operational_error())
@patch('db_client.Database.get_service_config', lambda **kwargs: mock_operational_error())
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_operation_error(*_args):
    """
    requirement: the initiate function has many SqlAlchemy operations - db connection errors most be caught
    mock: db_client to return OperationalError
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
             )
    )
    assert 'OperationalError' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs:
    type(
        "mockConfig", (object,),
        {"value": {"snApiUrl": True, "snAuthToken": True, "daysBack": 120, "MySupportSecretId": "test"}}
    )
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'vendor_netapp_api_client.NetAppApiClient.get_oath_cred',
    lambda *args, **kwargs:
    time.sleep(3)
)
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_lambda_timeout(*_args):
    """
    requirement: the initiate function may timeout if not completed within the max 900 seconds configured for most
                 lambda functions
    mock: LambdaTimeOutException after 2 sec ( 2000 ms )
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 2000
        }
             )
    )
    test = execution_message["message"]['errorType']
    assert 'LambdaTimeOutException' in test
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_service_config', lambda *args, **kwargs: False)
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
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
    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
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
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
def test_initiate_vendor_disabled(*_args):
    """
    requirement: the initiate function ensures that tha vendor is enabled in the DB and raises a VendorDisabled
                 exception when necessary

    mock: db_client to return disabled vendorEntry
    description: the execution should result with an operational error VendorDisabled
    :return:
    """
    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
             )
    )
    assert 'VendorDisabled' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
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
    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs:
    type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True, "daysBack": 120}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('boto3.client')
def test_initiate_missing_secret_name(*_args):
    """
    requirement: vendors supporting credentials are setup with AWS SecretManager secrets, the secret title is stored in
                 the service setting table and if missing for any reason a
    mock: db_client to return disabled vendorEntry ServiceNotConfigured should be raised
    description: the execution should result with an ServiceNotConfigured error
    :return:
    """
    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs:
    type("mockConfig", (object,),
         {"value": {
                  "snApiUrl": True, "snAuthToken": True, "daysBack": 120, "MySupportSecretId": "test",
                  "netAppPartnerCustomers": []
         }}
         )
)
@patch(
    'vendor_netapp_api_client.NetAppApiClient.generate_api_tokens', lambda *args, **kwargs: {"access_token": "test", }
)
@patch(
    'vendor_netapp_api_client.NetAppApiClient.get_oath_cred',
    lambda *args, **kwargs: {"setting-netapp-supportUser": "test", "setting-netapp-supportPass": "test"}
)
@patch('vendor_netapp_api_client.NetAppApiClient.consume_api', lambda *args, **kwargs: {"customers": {"list": []}})
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.update_account_customers', lambda *args, **kwargs: True)
@patch('boto3.client')
def test_initiate_missing_enabled_customers(*_args):
    """
    requirement: netapp Active IQ accounts manage multiple customers that are enabled/disabled in the database, if there
                 are no enabled customers, a ServiceNotConfigured should be raised
    mock: db_client to return disabled vendorEntry ServiceNotConfigured should be raised
    description: the execution should result with an ServiceNotConfigured error
    :return:
    """
    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('vendor_netapp_api_client.NetAppApiClient.bug_zero_vendor_status_update')
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs:
    type("mockConfig", (object,),
         {"value": {
             "snApiUrl": True, "snAuthToken": True, "daysBack": 120, "MySupportSecretId": "test",
             "netAppPartnerCustomers": [{"disabled": 0, "customerName": "test", "customerId": 1}]
         }}
         )
)
@patch(
    'vendor_netapp_api_client.NetAppApiClient.generate_api_tokens', lambda *args, **kwargs: {"access_token": "test", }
)
@patch(
    'vendor_netapp_api_client.NetAppApiClient.get_oath_cred',
    lambda *args, **kwargs: {"setting-netapp-supportUser": "test", "setting-netapp-supportPass": "test"}
)
@patch(
    'vendor_netapp_api_client.NetAppApiClient.consume_api',
    lambda *args, **kwargs:
    {"customers": {"list": []}, 'results': [{"model": "test", "system_id": "test", "version": "1"}]}
)
@patch('vendor_netapp_api_client.NetAppApiClient.authorize_bug_access', lambda *args, **kwargs: True)
@patch('vendor_netapp_api_client.NetAppApiClient.filter_risks', lambda *args, **kwargs: [])
@patch('vendor_netapp_api_client.NetAppApiClient.get_bugs_data', lambda *args, **kwargs: [])
@patch('vendor_netapp_api_client.NetAppApiClient.format_bug_entries', lambda *args, **kwargs: [])
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.update_account_customers', lambda *args, **kwargs: True)
@patch('db_client.Database.create_managed_product', lambda *args, **kwargs: mock_managed_product)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: [])
@patch('db_client.Database.insert_bug_updates', lambda *args, **kwargs: {"inserted_bugs": 0, "new_managed_products": 1})
@patch('boto3.client')
def test_initiate_no_bugs_inserted(*_args):
    """
    requirement: consume netapp API for account bugs ( all customers )
    mock: db_client to return disabled vendorEntry ServiceNotConfigured should be raised
    description: a successful execution with should result in a counter object returned
    :return:
    """
    from vendor_netapp_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        }
             )
    )
    assert not execution_message["message"]['inserted_bugs']

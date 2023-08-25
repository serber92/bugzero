"""
unit testing for vendor_aws_bug_service
"""
import os
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_operational_error, \
    mock_disabled_managed_product, mock_just_processed_managed_product, mock_database_init, mock_managed_product


########################################################################################################################
#                                                   initiate                                                           #
########################################################################################################################

@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: mock_operational_error())
@patch('db_client.Database.get_service_config', lambda **kwargs: mock_operational_error())
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
@patch('boto3.client')
def test_initiate_operation_error(*_args):
    """
    requirement: the initiate function has many SqlAlchemy operations - db connection errors most be caught
    mock: db_client to return OperationalError
    description: when trying to create a db session - an operationalError is returned
    :return:
    """

    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert 'OperationalError' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.get_service_config', lambda *args, **kwargs: False)
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
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
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
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
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
def test_initiate_vendor_disabled(*_args):
    """
    requirement: the initiate function ensures that tha vendor is enabled in the DB and raises a VendorDisabled
                 exception when necessary

    mock: db_client to return disabled vendorEntry
    description: the execution should result with an operational error VendorDisabled
    :return:
    """
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert 'VendorDisabled' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
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
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert 'ServiceNotConfigured' in execution_message["message"]['errorType']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: 0)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,), {"value": {"snApiUrl": True, "snAuthToken": True}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch(
    'db_client.Database.get_managed_products', lambda *args, **kwargs:
    {"Credentials": {"AccessKeyId": "", "SecretAccessKey": "", "SessionToken": ""}}
)
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
@patch('vendor_aws_api_client.AwsApiClient.get_account_service_count', lambda *_args, **_kwargs: [])
@patch('vendor_aws_health_client.HealthClient')
@patch('boto3.client')
def test_initiate_no_aws_discovered(*_args):
    """
    requirement: no supported aws services are found in the config aws accounts
    mock: managedProduct, vendor_aws_bug_service.sn_sync and bug_zero_vendor_status_update, sn query response
    description: iterating over the supported aws services, returning 0 resources, the process should complete without
                 adding new products or inserted new bugs
    :return:
    """
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert execution_message["message"] == 'There are no active and tagged aws services that match the vendor ' \
                                           'configuration'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: 0)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,),
                                 {"value": {"snApiUrl": True, "snAuthToken": True, "daysBack": 365}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_just_processed_managed_product)
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
@patch('vendor_aws_api_client.AwsApiClient.get_account_service_count', lambda *_args, **_kwargs: 1)
@patch('vendor_aws_health_client.HealthClient')
@patch('boto3.client')
def test_initiate_recently_processed_managed_products(*_args):
    """
    requirement: no supported aws services are found in the config aws accounts
    mock: managedProduct, vendor_aws_bug_service.sn_sync and bug_zero_vendor_status_update, sn query response
    description: iterating over the supported aws services, skipping recently processed managedProducts
    :return:
    """
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert execution_message["message"] == '0 new bugs published'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: 0)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,),
                                 {"value": {"snApiUrl": True, "snAuthToken": True, "daysBack": 365}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_disabled_managed_product)
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
@patch('vendor_aws_api_client.AwsApiClient.get_account_service_count', lambda *_args, **_kwargs: 1)
@patch('vendor_aws_health_client.HealthClient')
@patch('boto3.client')
def test_initiate_disabled_managed_products(*_args):
    """
    requirement: skipping disabled managedProducts
    mock: managedProduct, vendor_aws_bug_service.sn_sync and bug_zero_vendor_status_update, sn query response
    description: iterating over the supported aws services, skipping disabled managedProducts
    :return:
    """
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert execution_message["message"] == '0 new bugs published'
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
@patch('db_client.Database.create_session', lambda *args, **kwargs: True)
@patch('db_client.Database.remove_non_active_managed_products', lambda *args, **kwargs: 0)
@patch(
    'db_client.Database.get_service_config',
    lambda *args, **kwargs: type("mockConfig", (object,),
                                 {"value": {"snApiUrl": True, "snAuthToken": True, "daysBack": 365}})
)
@patch('db_client.Database.get_vendor_settings', lambda *args, **kwargs: True)
@patch('db_client.Database.get_managed_products', lambda *args, **kwargs: mock_managed_product)
@patch(
    'db_client.Database.insert_bug_updates', lambda *args, **kwargs:
    {"updated_bugs": 0, "inserted_bugs": 0, "skipped_bugs": 0}
)
@patch('vendor_aws_api_client.AwsApiClient.bug_zero_vendor_status_update')
@patch('vendor_aws_api_client.AwsApiClient.get_account_service_count', lambda *_args, **_kwargs: 1)
@patch('vendor_aws_api_client.AwsApiClient.format_bug_entry', lambda *_args, **_kwargs: False)
@patch('vendor_aws_health_client.HealthClient.describe_events', lambda *_args, **_kwargs: ["1", "2"])
@patch('boto3.client')
def test_initiate_no_bugs_found(*_args):
    """
    requirement: skip products if no bugs ( health events ) are found
    mock: vendor_aws_api_client.sn_sync and bug_zero_vendor_status_update
    description: return a 0 new bugs published message
    :return:
    """
    from vendor_aws_bug_service import initiate
    execution_message = initiate(
        "",
        type("MockContext", (object,), {"log_stream_name": "testing", "function_name": "dev-vendor-aws-bug-service",
                                        "log_group_name": "dev-vendor-aws-bug-service",
                                        "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
                                        }
             )
    )
    assert execution_message["message"] == '0 new bugs published'

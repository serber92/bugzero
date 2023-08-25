"""
unittest for vendor_netapp_api_client
"""
import datetime
import os
import sys
from unittest.mock import patch

import pytest

from tests.external_dependencies import MockNetAppApiClient, MockDbClientManagedProductsEmpty, mock_env, \
    mock_managed_products_2, netapp_bugs_missing_mandatory_field_examples, \
    netapp_bug_risks, netapp_valid_and_invalid_bug_examples, netapp_bug_risks_no_active_instances, \
    netapp_non_bug_risks, mock_operational_error, MockSecretManagerClient
from vendor_exceptions import ApiConnectionError, ApiResponseError, ApiAuthenticationError


########################################################################################################################
#                                           bug_zero_vendor_status_update                                              #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_bug_zero_vendor_status_update(*_args):
    """
    requirement: execute bug_zero_vendor_status_update successfully
    mock: db_client, **kwargs for bug_zero_vendor_status_update
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    instance = NetAppApiClient(vendor_id="rh")
    assert not instance.bug_zero_vendor_status_update(
        db_client=MockDbClientManagedProductsEmpty, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )

    del sys.modules['vendor_netapp_api_client']


########################################################################################################################
#                                                timestamp_format                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('sqlalchemy.orm.attributes', mock_operational_error)
@pytest.mark.parametrize(
    "time_str, expected_value",
    [
        ("2021-04-22T22:20:22Z",
         datetime.datetime.strptime("2021-04-22T22:20:22Z", "%Y-%m-%dT%H:%M:%SZ")),
        ("2021-05-22T22:20:22.000001Z",
         datetime.datetime.strptime("2021-05-22T22:20:22", "%Y-%m-%dT%H:%M:%S")),
        ("August 10, 2021",
         datetime.datetime.strptime("August 10, 2021", "%B %d, %Y")),
        ("2021-04-22",
         datetime.datetime.strptime("2021-04-22", "%Y-%m-%d")),
        ("bad-string", "bad-string")
    ]
)
def test_timestamp_format_scenarios(time_str, expected_value):
    """
    requirement: timestamp_format should return a datetime obj conforming to the passed string if the format is known
    or the string will be returned without being converted
    mock: time strings
    description: the known datetime strings format should return a datetime obj and the non-datetime string should be
    returned
    as is
    :param time_str:
    :param expected_value:
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    assert NetAppApiClient.timestamp_format(time_str=time_str) == expected_value


########################################################################################################################
#                                             generate_api_tokens                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
@patch(
    "requests.session"
)
def test_generate_api_tokens_api_authentication_error(*_args, **_kwargs):
    """
    requirement: of any of the login steps result in a connection error, a ApiAuthenticationError should be raised
    mock: NetAppApiClient, download_instance, netapp login credentials
    description: a false response will result in a ApiAuthenticationError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.generate_api_tokens(self=MockNetAppApiClient(), netapp_user="", netapp_password="")
        assert False
    except ApiAuthenticationError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockEmptyJsonResponse', (object,),
        {"text": b'{}', "url": "test"}
    )
)
def test_generate_api_tokens_empty_token_response(**_kwargs):
    """
    requirement: the last login step my resulted in an empty response that should raise an ApiAuthenticationError
    mock: NetAppApiClient, download_instance, netapp login credentials
    description: an empty response raising an ApiAuthenticationError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.generate_api_tokens(self=MockNetAppApiClient(), netapp_user="", netapp_password="")
        assert False
    except ApiAuthenticationError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockEmptyJsonResponse', (object,),
        {"text": b'non-json', "url": "test"}
    )
)
def test_generate_api_tokens_non_json_token_response(**_kwargs):
    """
    requirement: authentication error my result in a non-json response from the server
    mock: NetAppApiClient, download_instance, netapp login credentials
    description: an non-json response raising an ApiResponseError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.generate_api_tokens(self=MockNetAppApiClient(), netapp_user="", netapp_password="")
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']


########################################################################################################################
#                                              authorize_bug_access                                                    #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
@patch(
    "requests.session"
)
def test_authorize_bug_access_api_authentication_error(*_args, **_kwargs):
    """
    requirement: generate a session for authorized bug access and raise ApiAuthenticationError for connection errors
    mock: NetAppApiClient, download_instance, netapp login credentials
    description: a false response will result in a ApiAuthenticationError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.authorize_bug_access(self=MockNetAppApiClient(), netapp_user="", netapp_password="")
        assert False
    except ApiAuthenticationError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: True
)
@patch(
    "requests.session"
)
def test_authorize_bug_access(*_args, **_kwargs):
    """
    requirement: generate a session for authorized bug access and raise ApiAuthenticationError for connection errors
    mock: NetAppApiClient, download_instance, netapp login credentials
    description: a successful session creation should be completed without exception
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    NetAppApiClient.authorize_bug_access(self=MockNetAppApiClient(), netapp_user="", netapp_password="")
    assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']


########################################################################################################################
#                                                     get_bugs_data                                                    #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
@patch(
    "requests.session"
)
def test_get_bugs_data_api_connection_error(*_args, **_kwargs):
    """
    requirement: download bug data from netapp bug API and raise ApiConnectionError on connection errors
    mock: NetAppApiClient, download_instance, risks, customer_name
    description: a false response will result in a ApiConnectionError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        risks = [
            {"bug_api_url": "test", "bugId": "test"}
        ]
        NetAppApiClient.get_bugs_data(self=MockNetAppApiClient(), customer_name="", risks=risks)
        assert False
    except ApiConnectionError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockEmptyJsonResponse', (object,),
        {"text": b'non-json', "url": "test"}
    )
)
@patch(
    "requests.session"
)
def test_get_bugs_data_api_response_error(*_args, **_kwargs):
    """
    requirement: download bug data from netapp bug API and raise ApiResponseError on response parse errors
    mock: NetAppApiClient, download_instance, risks, customer_name
    description: a non-json response will result in a ApiResponseError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        risks = [
            {"bug_api_url": "test", "bugId": "test"}
        ]
        NetAppApiClient.get_bugs_data(self=MockNetAppApiClient(), customer_name="", risks=risks)
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockEmptyJsonResponse', (object,),
        {"text": b'{"valid_json": true}', "url": "test"}
    )
)
@patch(
    "requests.session"
)
def test_get_bugs_data_api(*_args, **_kwargs):
    """
    requirement: download bug data from netapp bug API
    mock: NetAppApiClient, download_instance, risks, customer_name
    description: a json response saved as a dict for each risk
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    risks = [
        {"bug_api_url": "test", "bugId": "test"},
        {"bug_api_url": "test2", "bugId": "test2"},
    ]
    risks = NetAppApiClient.get_bugs_data(self=MockNetAppApiClient(), customer_name="", risks=risks)
    risks = [x for x in risks if x["bug_data"]]
    assert len(risks) == 2


########################################################################################################################
#                                                     attach_managed_products                                          #
########################################################################################################################
def test_attach_managed_products_no_match_found(*_args, **_kwargs):
    """
    requirement: attach a managed product to a bug - matching both vendorPriorities and vendorStatuses
    mock: NetAppApiClient, managed_products, risk, bug_priority, bug_status
    description: mock_managed_products_2 does not have a matching managedProduct thus None should be returned
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    risk = {
        "affected_instances": [
            {"status": "active", "systemId": "sys3"}
        ]
    }
    assert not NetAppApiClient.attach_managed_products(
        self=MockNetAppApiClient(), managed_products=mock_managed_products_2, risk=risk, bug_priority="1",
        bug_status="1"
    )
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
def test_attach_managed_products(*_args, **_kwargs):
    """
    requirement: attach a managed product to a bug - matching both vendorPriorities and vendorStatuses
    mock: NetAppApiClient, managed_products, risk, bug_priority, bug_status
    description: mock_managed_products_2 has one matching managedProduct that should be returned
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    risk = {
        "affected_instances": [
            {"status": "active", "systemId": "sys1"}
        ]
    }
    managed_product = NetAppApiClient.attach_managed_products(
        self=MockNetAppApiClient(), managed_products=mock_managed_products_2, risk=risk, bug_priority="1",
        bug_status="1"
    )
    assert managed_product


########################################################################################################################
#                                                format_bug_entries                                                    #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_format_bug_entry_w_missing_mandatory_fields(*_args, **_kwargs):
    """
    requirement: mandatory bug fields should always exist and have a value in the formatted entry
    mock: bug examples with missing/empty random mandatory fields
    description: an empty list of bugs should be returned
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    assert NetAppApiClient.format_bug_entries(
        self=MockNetAppApiClient(), bugs=netapp_bugs_missing_mandatory_field_examples, customer_name="",
        managed_products="", bugs_days_back="", priority_map=""
    ) == []
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
def test_format_bug_entry_valid_and_invalid_bugs(*_args, **_kwargs):
    """
    requirement: mandatory bug fields should always exist and have a value in the formatted entry
    mock: bug examples with missing/empty random mandatory fields
    description: only valid bugs are returned
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    vendor_priority_map = {
        "P1": "Critical",
        "P2": "Major",
        "P3": "Minor",
        "P4": "Trivial",
        "P5": "Enhancement"
    }
    formatted_entries = NetAppApiClient.format_bug_entries(
        self=MockNetAppApiClient(), bugs=netapp_valid_and_invalid_bug_examples, customer_name="",
        managed_products="", bugs_days_back=99999, priority_map=vendor_priority_map
    )
    assert len(formatted_entries) == 3
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']


########################################################################################################################
#                                                      filter_risks                                                    #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_filter_risks_non_bug_risks(*_args, **_kwargs):
    """
    requirement: filter out netapp risks that don't include bug information
    mock: risk examples without bug information
    description: method returns an empty list
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    formatted_entries = NetAppApiClient.filter_risks(
        self=MockNetAppApiClient(), customer_name="", risks=netapp_non_bug_risks
    )
    assert not formatted_entries
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
def test_filter_bug_risks_no_affected_systems(*_args, **_kwargs):
    """
    requirement: filter out netapp bug risks that don't include active affected systems
    mock: bugs risks examples
    description: method returns an empty list
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    formatted_entries = NetAppApiClient.filter_risks(
        self=MockNetAppApiClient(), customer_name="", risks=netapp_bug_risks_no_active_instances
    )
    assert not formatted_entries
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
def test_filter_bug_risks(*_args, **_kwargs):
    """
    requirement: return risks with bug information and at least 1 active affected system
    mock: bugs risks examples
    description: return filtered bug risks
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    assert NetAppApiClient.filter_risks(
        self=MockNetAppApiClient(), customer_name="", risks=netapp_bug_risks
    )
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']


########################################################################################################################
#                                               get_oath_cred                                                          #
########################################################################################################################
def test_get_oath_cred_success(*_args):
    """
    requirement: return secret value from AWS SecretManager
    mock: Aws SecretManager client, NetAppApiClient
    description: return secret value
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    assert NetAppApiClient.get_oath_cred(
        MockSecretManagerClient(secret_binary=True, secret_string=True), secret_name=True
    ) == {'setting-netapp-supportUser': '1'}
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
def test_get_oath_client_error(*_args):
    """
    requirement: return secret value from AWS SecretManager
    mock: Aws SecretManager client, NetAppApiClient
    description: testing an exception ClientError from AWS SecretManager ( mock ) that should re-raised as
                 ApiConnectionError
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.get_oath_cred(
            MockSecretManagerClient(binary_error=True, secret_binary=True), secret_name=True
        )
        assert False
    except ApiConnectionError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_netapp_api_client']


########################################################################################################################
#                                               consume_api                                                            #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
@patch(
    "requests.get"
)
def test_consume_api_connection_error(*_args, **_kwargs):
    """
    requirement: consume API endpoint with a given endpoint url and access token and raise ApiConnectionError if needed
    mock: NetAppApiClient, download_instance
    description: the download instance is returned as false and thus the ApiConnectionError is raised
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.consume_api(self=MockNetAppApiClient(), endpoint_url="test-url", auth_token="")
        assert False
    except ApiConnectionError:
        assert True
    del sys.modules['vendor_netapp_api_client']
    del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type("nonJsonResponse", (object,), {"text": b'non-json', "url": "test"})
)
@patch(
    "requests.get"
)
def test_consume_api_response_error(*_args, **_kwargs):
    """
    requirement: consume API endpoint with a given endpoint url and access token and raise ApiResponseError if needed
    mock: NetAppApiClient, download_instance
    description: the request text is a non-json string that
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.consume_api(self=MockNetAppApiClient(), endpoint_url="test-url", auth_token="")
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_netapp_api_client']


########################################################################################################################
#                                               get_account_customers                                                  #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
@patch(
    "requests.get"
)
def test_get_account_customers_api_connection_error(*_args, **_kwargs):
    """
    requirement: retrieve account costumers from netapp Active IQ API
    mock: NetAppApiClient, download_instance
    description: raise ApiConnectionError on connection errors
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.get_account_customers(self=MockNetAppApiClient(), auth_token="")
        assert False
    except ApiConnectionError:
        assert True
    del sys.modules['vendor_netapp_api_client']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type("nonJsonResponse", (object,), {"text": b'non-json', "url": "test"})
)
@patch(
    "requests.get"
)
def test_get_account_customers_api_response_error(*_args, **_kwargs):
    """
    requirement: retrieve account costumers from netapp Active IQ API
    mock: NetAppApiClient, download_instance
    description: raise ApiResponseError if non-json string is returned in the response body
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    try:
        NetAppApiClient.get_account_customers(self=MockNetAppApiClient(), auth_token="")
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_netapp_api_client']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type("nonJsonResponse", (object,),
                          {"text": b'{"customers": {"list": [{"systemCount": 1}]}}', "url": "test"})
)
@patch(
    "requests.get"
)
def test_get_account_customers_api(*_args, **_kwargs):
    """
    requirement: retrieve account costumers from netapp Active IQ API
    mock: NetAppApiClient, download_instance
    description: raise ApiResponseError if non-json string is returned in the response body
    :return:
    """
    from vendor_netapp_api_client import NetAppApiClient
    customers = NetAppApiClient.get_account_customers(self=MockNetAppApiClient(), auth_token="")
    assert customers
    del sys.modules['vendor_netapp_api_client']

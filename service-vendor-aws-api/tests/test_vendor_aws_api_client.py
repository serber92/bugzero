"""
unittest for vendor_aws_api_client
"""
import datetime
import os
from unittest.mock import patch

import pytest

from tests.external_dependencies import mock_env, MockAwsApiClient, mock_managed_product, mock_database_init, \
    mock_operational_error, mock_health_events_different_event_scope, mock_health_events_different_priorities, \
    mock_health_events_old_entries, mock_health_events_different_status, mock_health_events_different_region, \
    mock_health_events
from vendor_exceptions import ApiConnectionError, ApiResponseError


########################################################################################################################
#                                                format_bug_entry                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, health_event",
    [
        (MockAwsApiClient(), mock_health_events_different_event_scope[0]),
        (MockAwsApiClient(), mock_health_events_different_event_scope[1]),
        (MockAwsApiClient(), mock_health_events_different_event_scope[2]),
        (MockAwsApiClient(), mock_health_events_different_event_scope[3]),
        (MockAwsApiClient(), mock_health_events_different_event_scope[4])
    ]
)
def test_format_bug_entry_filter_event_scope(self, health_event):
    """
    requirement: health events scopes must match the managedProduct configured scopes
    description: when filtering health events per managedProduct, events categories must match the categories
                 configured for a given managed product or it will be skipped ( false returned from function )
    mock: MockAwsApiClient, health events, managed product, last execution
    :param self:
    :param health_event:
    :return:
    """
    last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    from vendor_aws_api_client import AwsApiClient
    assert not AwsApiClient.format_bug_entry(
        self=self, health_event=health_event, managed_product=mock_managed_product[0], last_execution=last_execution
    )


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, health_event",
    [
        (MockAwsApiClient(), mock_health_events_different_priorities[0]),
        (MockAwsApiClient(), mock_health_events_different_priorities[1]),
        (MockAwsApiClient(), mock_health_events_different_priorities[2]),
        (MockAwsApiClient(), mock_health_events_different_priorities[3]),
        (MockAwsApiClient(), mock_health_events_different_priorities[4])
    ]
)
def test_format_bug_entry_filter_priority(self, health_event):
    """
    requirement: health events scopes must match the managedProduct configured priorities
    description: when filtering health events per managedProduct, events priorities must match the priorities
                 configured for a given managed product or it will be skipped ( false returned from function )
    mock: MockAwsApiClient, health events, managed product, last execution
    :param self:
    :param health_event:
    :return:
    """
    last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    from vendor_aws_api_client import AwsApiClient
    assert not AwsApiClient.format_bug_entry(
        self=self, health_event=health_event, managed_product=mock_managed_product[0], last_execution=last_execution
    )


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, health_event",
    [
        (MockAwsApiClient(), mock_health_events_old_entries[0]),
        (MockAwsApiClient(), mock_health_events_old_entries[1]),
        (MockAwsApiClient(), mock_health_events_old_entries[2]),
        (MockAwsApiClient(), mock_health_events_old_entries[3]),
        (MockAwsApiClient(), mock_health_events_old_entries[4])
    ]
)
def test_format_bug_entry_old_entries(self, health_event):
    """
    requirement: health events scopes must not be older than managedProduct.lastExecution variable
    description: when filtering health events per managedProduct, events priorities must match the priorities
                 configured for a given managed product or it will be skipped ( false returned from function )
    mock: MockAwsApiClient, health events, managed product, last execution
    :param self:
    :param health_event:
    :return:
    """
    last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    from vendor_aws_api_client import AwsApiClient
    assert not AwsApiClient.format_bug_entry(
        self=self, health_event=health_event, managed_product=mock_managed_product[0], last_execution=last_execution
    )


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, health_event",
    [
        (MockAwsApiClient(), mock_health_events_different_status[0]),
        (MockAwsApiClient(), mock_health_events_different_status[1]),
        (MockAwsApiClient(), mock_health_events_different_status[2]),
        (MockAwsApiClient(), mock_health_events_different_status[3]),
        (MockAwsApiClient(), mock_health_events_different_status[4])
    ]
)
def test_format_bug_entry_filter_status(self, health_event):
    """
    requirement: health events status must match the managedProduct.vendorStatuses variable
    description: when filtering health events per managedProduct, events statuses must match the statuses
                 configured for a given managed product or it will be skipped ( false returned from function )
    mock: MockAwsApiClient, health events, managed product, last execution
    :param self:
    :param health_event:
    :return:
    """
    last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    from vendor_aws_api_client import AwsApiClient
    assert not AwsApiClient.format_bug_entry(
        self=self, health_event=health_event, managed_product=mock_managed_product[0], last_execution=last_execution
    )


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, health_event",
    [
        (MockAwsApiClient(), mock_health_events_different_region[0]),
        (MockAwsApiClient(), mock_health_events_different_region[1]),
        (MockAwsApiClient(), mock_health_events_different_region[2]),
        (MockAwsApiClient(), mock_health_events_different_region[3]),
        (MockAwsApiClient(), mock_health_events_different_region[4])
    ]
)
def test_format_bug_entry_filter_region(self, health_event):
    """
    requirement: health events region must match the managedProduct configured regions
    description: when filtering health events per managedProduct, events regions must match the regopms
                 configured for a given managed product or it will be skipped ( false returned from function )
    mock: MockAwsApiClient, health events, managed product, last execution
    :param self:
    :param health_event:
    :return:
    """
    last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    from vendor_aws_api_client import AwsApiClient
    assert not AwsApiClient.format_bug_entry(
        self=self, health_event=health_event, managed_product=mock_managed_product[0], last_execution=last_execution
    )


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, health_event",
    [
        (MockAwsApiClient(), mock_health_events[0]),
        (MockAwsApiClient(), mock_health_events[1]),
        (MockAwsApiClient(), mock_health_events[2]),
        (MockAwsApiClient(), mock_health_events[3]),
        (MockAwsApiClient(), mock_health_events[4])
    ]
)
def test_format_bug_entry(self, health_event):
    """
    requirement: format relevant health events as bugs
    description: generate the right data fields for health events as bugs
    mock: MockAwsApiClient, health events, managed product, last execution
    :param self:
    :param health_event:
    :return:
    """
    last_execution = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    from vendor_aws_api_client import AwsApiClient
    assert AwsApiClient.format_bug_entry(
        self=self, health_event=health_event, managed_product=mock_managed_product[0], last_execution=last_execution
    )


########################################################################################################################
#                                           bug_zero_vendor_status_update                                              #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('db_client.Database.__init__', new=mock_database_init)
def test_bug_zero_vendor_status_update(*_args):
    """
    requirement: execute bug_zero_vendor_status_update successfully
    mock: db_client, **kwargs for bug_zero_vendor_status_update
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    from db_client import Database

    instance = AwsApiClient(vendor_id="aws")
    db_client = Database(db_user="", db_name="", db_port="3660", db_host="", db_password="")
    assert not instance.bug_zero_vendor_status_update(
        db_client=db_client, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )


########################################################################################################################
#                                                timestamp_format                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('sqlalchemy.orm.attributes', mock_operational_error)
@pytest.mark.parametrize(
    "time_str, expected_value",
    [
        ("2021-04-22",
         datetime.datetime.strptime("2021-04-22", "%Y-%m-%d")),
        ("2021-05-22T22:20:22.000001Z",
         datetime.datetime.strptime("2021-05-22T22:20:22.000001Z", "%Y-%m-%dT%H:%M:%S.%fZ")),
        ("Sun, 10 Aug 2021 22:20:22Z",
         datetime.datetime.strptime("Sun, 10 Aug 2021 22:20:22Z", "%a, %d %b %Y %H:%M:%SZ")),
        ("Sun, 10 Aug 2021 22:20:22Z",
         datetime.datetime.strptime("Sun, 10 Aug 2021 22:20:22Z", "%a, %d %b %Y %H:%M:%SZ")),
        ("bad-string", "bad-string")
    ]
)
def test_timestamp_format_scenarios(time_str, expected_value):
    """
    requirement: timestamp_format should return a datetime obj conforming to the passed string if the format is known
    or the string will be returned without being converted
    mock: time strings
    description: the known datetime strings format should return a datetime obj and the non-datetime string should be
    returned as is
    :param time_str:
    :param expected_value:
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    assert AwsApiClient.timestamp_format(time_str=time_str) == expected_value


########################################################################################################################
#                                                          sn_sync                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('requests.request', lambda **_kwargs: type("request", (object,), {"status_code": 500, "url": "test"}))
def test_sn_sync_api_connection_error(**_kwargs):
    """
    requirement: if serviceNow API request fails a custom ApiConnectionError should be raised
    mock: AwsApiClient, download_instance, sn_sync **_kwargs
    description: the download instance is returned as false and thus the ApiConnectionError is raised
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        AwsApiClient.sn_sync(
            self=MockAwsApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
        )
        assert False
    except ApiConnectionError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test", "text": b'non-json-string', "headers": {"x-total-count": 1}})
)
def test_sn_sync_api_response_error(**_kwargs):
    """
    requirement: if serviceNow API response is a non-json string the JSONDecodeError will re-raise a custom
                 ApiConnectionError
    mock: AwsApiClient, download_instance, sn_sync **_kwargs
    description: JSONDecodeError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        AwsApiClient.sn_sync(
            self=MockAwsApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
        )
        assert False
    except ApiResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs: type("request", (object,),
                           {"status_code": 200, "url": "test", "text": b'non-json-string', "headers": {}})
)
def test_sn_sync_api_response_missing_count_header(**_kwargs):
    """
    requirement: serviceNow api should returned an cmdb_ci 'x-total-count' headers, if missing an ApiResponseError
                 should be raised
    mock: VeeamApiClient, download_instance, sn_sync **_kwargs
    description: KeyError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        AwsApiClient.sn_sync(
            self=MockAwsApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
        )
        assert False
    except ApiResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch('requests.request',
       lambda **_kwargs: type("request", (object,), {
           "status_code": 200, "url": "test",
           "text": b'{"result": [{"os_version": 1.1}, {"os_version": 2.2}, {"os_version": 3.3}, {"os_version": 4.4}]}',
           "headers": {"x-total-count": 4}
       }))
def test_sn_sync_api(**_kwargs):
    """
    requirement: run sn sync an populated the passed query_product with a list of unique 'sn_ci_versions'
    mock: VeeamApiClient, download_instance, sn_sync **_kwargs
    description: mock a download response that returns 4 unique ci_cmdb versions
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    instances = AwsApiClient.sn_sync(
        self=MockAwsApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
    )
    assert len(instances) == 4


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test",  "text": b'{"result": []}', "headers": {"x-total-count": 0}
    })
)
def test_sn_sync_api_no_cis_found(**_kwargs):
    """
    requirement: run sn sync an populated the passed query_product with a list of unique 'sn_ci_versions'
    mock: VeeamApiClient, download_instance, sn_sync **_kwargs
    description: mock a download response that simulates that no CIs were found
    :return:
    """
    from vendor_aws_api_client import AwsApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    instances = AwsApiClient.sn_sync(
        self=MockAwsApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
    )
    assert not instances

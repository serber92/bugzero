"""
unittest for vendor_rh_api_client
"""
import datetime
import os
import sys
from unittest.mock import patch

import pytest
from vendor_rh_exceptions import ApiConnectionError, ApiResponseError

from tests.external_dependencies import MockRhApiClient, MockDbClientManagedProductsEmpty, mock_env, \
    rh_bugs_w_versions_examples, rh_bugs_missing_mandatory_field_examples, rh_bugs_valid_and_invalid_examples, \
    mock_rh_managed_product, mock_operational_error


########################################################################################################################
#                                                format_bug_entry                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug, empty_list",
    [
        (MockRhApiClient(), rh_bugs_w_versions_examples[0], []),
        (MockRhApiClient(), rh_bugs_w_versions_examples[1], []),
        (MockRhApiClient(), rh_bugs_w_versions_examples[2], []),
        (MockRhApiClient(), rh_bugs_w_versions_examples[3], []),
        (MockRhApiClient(), rh_bugs_w_versions_examples[4], [])
    ]
)
def test_format_bug_entry_no_version(self, single_bug, empty_list):
    """
    requirement: retrieved bugs should have values in the 'version' field so it could be attached to a snCI
    mock: bug examples with empty version field
    description: trying to format bugs with empty 'version' field should return an empty list
    :param self:
    :param single_bug:
    :param empty_list:
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    assert RedHatApiClient.format_bug_entry(
        self=self, bugs=single_bug, managed_product=mock_rh_managed_product, sn_ci_filter="testFilter",
        service_now_ci_table="testTable"
    ) == empty_list
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_rh_api_client']


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug",
    [
        (MockRhApiClient(), rh_bugs_missing_mandatory_field_examples[0]),
        (MockRhApiClient(), rh_bugs_missing_mandatory_field_examples[1]),
        (MockRhApiClient(), rh_bugs_missing_mandatory_field_examples[2]),
        (MockRhApiClient(), rh_bugs_missing_mandatory_field_examples[3]),
        (MockRhApiClient(), rh_bugs_missing_mandatory_field_examples[4]),
    ]
)
def test_format_bug_entry_w_missing_mandatory_fields(self, single_bug):
    """
    requirement: mandatory bug fields should always exist and have a value in the formatted entry
    mock: bug examples with missing/empty random mandatory fields
    description: an empty list of bugs should be returned
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    assert RedHatApiClient.format_bug_entry(
        self=self, bugs=single_bug, managed_product=mock_rh_managed_product, sn_ci_filter="testFilter",
        service_now_ci_table="testTable"
    ) == []
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_rh_api_client']


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug, result",
    [
        (MockRhApiClient(), rh_bugs_valid_and_invalid_examples[0], 1),
        (MockRhApiClient(), rh_bugs_valid_and_invalid_examples[1], 0),
        (MockRhApiClient(), rh_bugs_valid_and_invalid_examples[2], 1),
        (MockRhApiClient(), rh_bugs_valid_and_invalid_examples[3], 0),
        (MockRhApiClient(), rh_bugs_valid_and_invalid_examples[4], 1),
    ]
)
def test_format_bug_entry(self, single_bug, result):
    """
    requirement: mandatory bug fields should always exist and have a value in the formatted entry, version field should
    mock: 5 valid bug examples + 5 invalid bug with random issues
    description: return a list with 1 entry for valid bugs and an empty list for invalid bugs
    :param self:
    :param single_bug:
    :param result:
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    formatted_entry = RedHatApiClient.format_bug_entry(
        self=self, bugs=single_bug, managed_product=mock_rh_managed_product, sn_ci_filter="testFilter",
        service_now_ci_table="testTable")
    assert len(formatted_entry) == result
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_rh_api_client']


#######################################################################################################################
#                                               get_bugs                                                              #
#######################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
def test_get_bugs_api_connection_error(**_kwargs):
    """
    requirement: if Redhat bugzilla API request fails a custom ApiConnectionError should be raised
    mock: RedHatApiClient, download_instance
    description: the download instance is returned as false and thus the ApiConnectionError is raised
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    try:
        RedHatApiClient.get_bugs(self=MockRhApiClient(), search_url="test-url", product_name="testProduct")
        assert False
    except ApiConnectionError:
        assert True
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockNonJsonResponse', (object,),
        {"text": b'non-json-string'}
    )
)
def test_get_bugs_api_response_error(**_kwargs):
    """
    requirement: if Redhat bugzilla API response body is a non-json string
    mock: RedHatApiClient, download_instance
    description: the download instance is returned with a non-json string and ApiResponseError will be raised from
                 the original JSONDecodeError
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    try:
        RedHatApiClient.get_bugs(self=MockRhApiClient(), search_url="test-url", product_name="testProduct")
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockNonJsonResponse', (object,),
        {"text": b'{"bugs": [1, 2, 3, 4, 5], "total_matches": 5}'}
    )
)
def test_get_bugs(**_kwargs):
    """
    requirement: a valid api request should return a list of bugs based on the search url
    mock: RedHatApiClient, download_instance
    description: the api returns 5 bugs from a total of 5 bugs thus a list of 5 bugs should be returned to the caller
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    bugs = RedHatApiClient.get_bugs(self=MockRhApiClient(), search_url="test-url", product_name="testProduct")
    assert len(bugs) == 5
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


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
    from vendor_rh_api_client import RedHatApiClient
    instance = RedHatApiClient(vendor_id="rh")
    assert not instance.bug_zero_vendor_status_update(
        db_client=MockDbClientManagedProductsEmpty, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )

    del sys.modules['vendor_rh_api_client']


########################################################################################################################
#                                                          sn_sync                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: False
)
def test_sn_sync_api_connection_error(**_kwargs):
    """
    requirement: if serviceNow API request fails a custom ApiConnectionError should be raised
    mock: RedHatApiClient, download_instance, sn_sync **_kwargs
    description: the download instance is returned as false and thus the ApiConnectionError is raised
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    query_product = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": ""
    }
    try:
        RedHatApiClient.sn_sync(self=MockRhApiClient(), query_product=query_product, sn_auth_token="", sn_api_url="")
        assert False
    except ApiConnectionError:
        assert True
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockNonJsonResponse', (object,),
        {"text": b'non-json-string', "headers": {"x-total-count": 1}}
    )
)
def test_sn_sync_api_response_error(**_kwargs):
    """
    requirement: if serviceNow API response is a non-json string the JSONDecodeError will re-raise a custom
                 ApiConnectionError
    mock: RedHatApiClient, download_instance, sn_sync **_kwargs
    description: JSONDecodeError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    query_product = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": ""
    }
    try:
        RedHatApiClient.sn_sync(self=MockRhApiClient(), query_product=query_product, sn_auth_token="", sn_api_url="")
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockNonJsonResponse', (object,),
        {"text": b'non-json-string', "headers": {}}
    )
)
def test_sn_sync_api_response_missing_count_header(**_kwargs):
    """
    requirement: serviceNow api should returned an cmdb_ci 'x-total-count' headers, if missing an ApiResponseError
                 should be raised
    mock: RedHatApiClient, download_instance, sn_sync **_kwargs
    description: KeyError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    query_product = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": ""
    }
    try:
        RedHatApiClient.sn_sync(self=MockRhApiClient(), query_product=query_product, sn_auth_token="", sn_api_url="")
        assert False
    except ApiResponseError:
        assert True
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockNonJsonResponse', (object,),
        {
            "text": b'{"result": [{"os_version": 1.1}, {"os_version": 2.2}, {"os_version": 3.3}, {"os_version": 4.4}]}',
            "headers": {"x-total-count": 5}}
    )
)
def test_sn_sync_api(**_kwargs):
    """
    requirement: run sn sync an populated the passed query_product with a list of unique 'sn_ci_versions'
    mock: RedHatApiClient, download_instance, sn_sync **_kwargs
    description: mock a download response that returns 4 unique ci_cmdb versions
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    query_product = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": ""
    }
    query_product = RedHatApiClient.sn_sync(
        self=MockRhApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
    )
    assert len(query_product['sn_ci_versions']) == 4
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockNonJsonResponse', (object,),
        {
            "text": b'{"result": []}',
            "headers": {"x-total-count": 0}}
    )
)
def test_sn_sync_api_no_cis_found(**_kwargs):
    """
    requirement: run sn sync an populated the passed query_product with a list of unique 'sn_ci_versions'
    mock: RedHatApiClient, download_instance, sn_sync **_kwargs
    description: mock a download response that simulates that no CIs were found
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    query_product = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": ""
    }
    query_product = RedHatApiClient.sn_sync(
        self=MockRhApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
    )
    assert not query_product['sn_ci_versions']
    del sys.modules['vendor_rh_api_client']
    del sys.modules['download_manager']


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
        ("Sun, 10 Aug 2021 22:20:22 Z",
         datetime.datetime.strptime("Sun, 10 Aug 2021 22:20:22 Z", "%a, %d %b %Y %H:%M:%S Z")),
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
    returned
    as is
    :param time_str:
    :param expected_value:
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    assert RedHatApiClient.timestamp_format(time_str=time_str) == expected_value


########################################################################################################################
#                                                generate_api_search_url                                               #
########################################################################################################################
@pytest.mark.parametrize(
    "name, vendor_priorities, vendor_statuses, vendor_resolutions, versions, start_date, end_date, expected_search_url",
    [
        ("Product 1",
         [{'vendorPriority': "Priority 1"}, {'vendorPriority': "Priority 2"}],
         ["Status 1", "Status 2"],
         ["Resolution 1", "Resolution 2"],
         ["2.2", "3.3"],
         "2022-01-01",
         "2022-02-02",
         "https://bugzilla.redhat.com/rest/bug?product=Product 1&chfieldfrom=2022-01-01&chfieldto=2022-02-02"
         "&include_fields=product,id,description,summary,version,status,priority,last_change_time,creation_time,op_sys"
         ",votes,cf_fixed_in,longdescs.count&bug_status=Status 1&bug_status=Status 2&priority=Priority 1"
         "&priority=Priority 2&version=2.2&version=3.3&resolution=Resolution 1&resolution=Resolution 2&resolution=---"
         ),
        ("Product 2",
         [{'vendorPriority': "Priority 3"}, {'vendorPriority': "Priority 4"}],
         ["Status 3", "Status 4"],
         ["Resolution 3", "Resolution 4"],
         ["4.4", "5.5"],
         "2022-03-03",
         "2022-04-04",
         "https://bugzilla.redhat.com/rest/bug?product=Product 2&chfieldfrom=2022-03-03&chfieldto=2022-04-04"
         "&include_fields=product,id,description,summary,version,status,priority,last_change_time,creation_time,op_sys"
         ",votes,cf_fixed_in,longdescs.count&bug_status=Status 3&bug_status=Status 4&priority=Priority 3"
         "&priority=Priority 4&version=4.4&version=5.5&resolution=Resolution 3&resolution=Resolution 4&resolution=---"
         ),
        ("Product 3",
         [{'vendorPriority': "Priority 5"}, {'vendorPriority': "Priority 6"}],
         ["Status 5", "Status 6"],
         ["Resolution 5", "Resolution 6"],
         ["6.6", "7.7"],
         "2022-05-05",
         "2022-06-06",
         "https://bugzilla.redhat.com/rest/bug?product=Product 3&chfieldfrom=2022-05-05&chfieldto=2022-06-06"
         "&include_fields=product,id,description,summary,version,status,priority,last_change_time,creation_time,op_sys"
         ",votes,cf_fixed_in,longdescs.count&bug_status=Status 5&bug_status=Status 6&priority=Priority 5"
         "&priority=Priority 6&version=6.6&version=7.7&resolution=Resolution 5&resolution=Resolution 6&resolution=---"
         )
    ]
)
def test_generate_api_search_url(
        name, vendor_priorities, vendor_statuses, vendor_resolutions, versions, start_date, end_date,
        expected_search_url
):
    """
    requirement: generate a Red Hat Bugzilla API search url based on existing managedProducts / Vendor Settings
    mock: RedHatApiClient, download_instance, generate_api_search_url **_kwargs
    description: provide config variables and expected generated url
    :return:
    """
    from vendor_rh_api_client import RedHatApiClient
    search_url = RedHatApiClient.generate_api_search_url(
        self=MockRhApiClient(), name=name, vendor_priorities=vendor_priorities, vendor_statuses=vendor_statuses,
        vendor_resolutions=vendor_resolutions, versions=versions, start_date=start_date, end_date=end_date
    )
    assert search_url == expected_search_url
    del sys.modules['vendor_rh_api_client']

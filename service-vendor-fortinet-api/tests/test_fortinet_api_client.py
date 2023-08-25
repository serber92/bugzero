"""
unittest for vendor_fortinet_api_client
"""
import datetime
import os
from unittest.mock import patch

import pytest

from tests.external_dependencies import mock_env, MockFortinetApiClient, mock_managed_product, \
    mock_formatted_bugs, mock_database_init, mock_formatted_mandatory_fields_missing, mock_operational_error
from vendor_exceptions import ApiConnectionError, ApiResponseError, VendorConnectionError, VendorResponseError


########################################################################################################################
#                                                format_bug_entry                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug, empty_list",
    [
        (MockFortinetApiClient(), mock_formatted_mandatory_fields_missing[0], []),
        (MockFortinetApiClient(), mock_formatted_mandatory_fields_missing[1], []),
        (MockFortinetApiClient(), mock_formatted_mandatory_fields_missing[2], []),
        (MockFortinetApiClient(), mock_formatted_mandatory_fields_missing[3], []),
        (MockFortinetApiClient(), mock_formatted_mandatory_fields_missing[4], [])
    ]
)
def test_format_bug_entry_missing_mandatory_field(self, single_bug, empty_list):
    """
    requirement: formatted bugs must have two mandatory fields ["bugId", "description]
    description: bugs missing any mandatory fields should be skipped, the testing case should return an empty list
    mock: bugs, db_client, FortinetApiClient
    :param self:
    :param single_bug:
    :param empty_list:
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    assert FortinetApiClient.format_bug_entry(
        self=self, bugs=single_bug, managed_product=mock_managed_product[0], sn_ci_filter="testFilter",
        sn_ci_table="testTable", os_version=["testVersion-1", "testVersion-2"]
    ) == empty_list


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug",
    [
        (MockFortinetApiClient(), mock_formatted_bugs[0]),
        (MockFortinetApiClient(), mock_formatted_bugs[1]),
        (MockFortinetApiClient(), mock_formatted_bugs[2]),
        (MockFortinetApiClient(), mock_formatted_bugs[3]),
        (MockFortinetApiClient(), mock_formatted_bugs[4])
    ]
)
def test_format_bug_successful(self, single_bug):
    """
    requirement: formatted bugs must have two mandatory fields ["bugId", "description]
    description: valid bugs should be processed and return a list with values
    mock: bugs, db_client, FortinetApiClient
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    execution = FortinetApiClient.format_bug_entry(
        self=self, bugs=single_bug, managed_product=mock_managed_product[0], sn_ci_filter="testFilter",
        sn_ci_table="testTable", os_version=["testVersion-1", "testVersion-2"]
    )
    assert len(execution) == 1


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
    from vendor_fortinet_api_client import FortinetApiClient
    from db_client import Database

    instance = FortinetApiClient(vendor_id="fortinet")
    db_client = Database(db_user="", db_name="", db_port="3660", db_host="", db_password="")
    assert not instance.bug_zero_vendor_status_update(
        db_client=db_client, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )


########################################################################################################################
#                                                          sn_sync                                                     #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('requests.request', lambda **_kwargs: type("request", (object,), {"status_code": 500, "url": "test"}))
def test_sn_sync_api_connection_error(**_kwargs):
    """
    requirement: if serviceNow API request fails a custom ApiConnectionError should be raised
    mock: FortinetApiClient, download_instance, sn_sync **_kwargs
    description: the download instance is returned as false and thus the ApiConnectionError is raised
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    product_type = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": ""
    }
    try:
        FortinetApiClient.sn_sync(
            self=MockFortinetApiClient(), product_type=product_type, sn_auth_token="", sn_api_url=""
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
    mock: FortinetApiClient, download_instance, sn_sync **_kwargs
    description: JSONDecodeError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    product_type = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": "", "type": "Fortinet Firewalls"
    }
    try:
        FortinetApiClient.sn_sync(
            self=MockFortinetApiClient(), product_type=product_type, sn_auth_token="", sn_api_url=""
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
    mock: FortinetApiClient, download_instance, sn_sync **_kwargs
    description: KeyError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    product_type = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": "", "type": "Fortinet Firewalls"
    }
    try:
        FortinetApiClient.sn_sync(
            self=MockFortinetApiClient(), product_type=product_type, sn_auth_token="", sn_api_url=""
        )
        assert False
    except ApiResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch('requests.request',
       lambda **_kwargs: type("request", (object,), {
           "status_code": 200, "url": "test",
           "text": b'{"result": [{"os_version": 1.1}, {"os_version": 2.2}, {"os_version": 3.3}, {"os_version": 4.4}]}',
           "headers": {"x-total-count": 5}
       }))
def test_sn_sync_api(**_kwargs):
    """
    requirement: run sn sync an populated the passed query_product with a list of unique 'sn_ci_versions'
    mock: FortinetApiClient, download_instance, sn_sync **_kwargs
    description: mock a download response that returns 4 unique ci_cmdb versions
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    product_type = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": "", "type": "Fortinet Firewalls"
    }
    instances = FortinetApiClient.sn_sync(
        self=MockFortinetApiClient(), product_type=product_type, sn_auth_token="", sn_api_url=""
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
    mock: FortinetApiClient, download_instance, sn_sync **_kwargs
    description: mock a download response that simulates that no CIs were found
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    product_type = {
        "sysparm_fields": "", "sysparm_query": "", "service_now_ci_table": "", "value": "", "type": "Fortinet Firewalls"
    }
    instances = FortinetApiClient.sn_sync(
        self=MockFortinetApiClient(), product_type=product_type, sn_auth_token="", sn_api_url=""
    )
    assert not instances


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
    returned
    as is
    :param time_str:
    :param expected_value:
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    assert FortinetApiClient.timestamp_format(time_str=time_str) == expected_value


########################################################################################################################
#                                                generate_release_notes_urls                                           #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"})
)
def test_generate_release_notes_urls_download_error(**_kwargs):
    """
    requirement: 1.download a given product documentation landing page
                 2.parse out release notes urls for all versions in the page
    mock: FortinetApiClient, download_instance
    description: download error of product landing page should raise a VendorConnectionError exception
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    try:
        FortinetApiClient.generate_release_notes_urls(
            self=MockFortinetApiClient(), product_slug_name="test-product", product_name="Test Product"
        )
        assert False
    except VendorConnectionError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test", "text": "test"})
)
def test_generate_release_notes_urls_missing_release_notes(**_kwargs):
    """
    requirement: 1.download a given product documentation landing page
                 2.parse out release notes urls for all versions in the page
    mock: FortinetApiClient, download_instance
    description: return a false value when the release notes page xpath returns empty
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    execution = FortinetApiClient.generate_release_notes_urls(
        self=MockFortinetApiClient(), product_slug_name="test-product", product_name="Test Product"
    )
    assert not execution


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs:
    type("request", (object,),
         {
             "status_code": 200,
             "url": "test",
             "text": "<html><body><div class='version-dropdown'><div class='version-item'> <a href='test-url'>1.0.0"
                     "</a><a href='test-url'>1.1.1</a> </div></div><div><a href='test-url'>Release Notes</a><h3>"
                     "<a href='test-url'>Release Notes</a></h3></div></body></html>"
         })
)
def test_generate_release_notes_urls(**_kwargs):
    """
    requirement: 1.download a given product documentation landing page
                 2.parse out release notes urls for all versions in the page
    mock: FortinetApiClient, download_instance
    description: return a list of version + url dictionaries ( len == 2 )
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    release_notes_list = FortinetApiClient.generate_release_notes_urls(
        self=MockFortinetApiClient(), product_slug_name="test-product", product_name="Test Product"
    )
    assert len(release_notes_list) == 2


#######################################################################################################################
#                                               get_bugs                                                              #
#######################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('requests.request', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
def test_get_bugs_connection_error(**_kwargs):
    """
    requirement: if a product release note html request fails, a custom VendorConnectionError should be raised
    mock: FortinetApiClient, download_instance
    description: the download instance is returned as false and thus the VendorConnectionError is raised
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    try:
        FortinetApiClient.get_bugs(
            self=MockFortinetApiClient(),
            release_notes_url="test-url", product_name="Test Product", product_version="1.0.0"
        )
        assert False
    except VendorConnectionError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test", "text": b'<html></html>'})
)
def test_get_bugs_api_missing_data_pages(**_kwargs):
    """
    requirement: return an empty list if both known and resolved issues xpaths lookup return false
    mock: FortinetApiClient, download_instance
    description: the release notes page does not include known and resolved issues elements and thus bugs could not be
                 retrieved for the given product version
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    bugs = FortinetApiClient.get_bugs(
            self=MockFortinetApiClient(),
            release_notes_url="test-url", product_name="Test Product", product_version="1.0.0"
        )
    assert not bugs


@patch.dict(os.environ, mock_env())
@patch(
        'requests.request',
        lambda **_kwargs:
        type("request", (object,),
             {
                 "status_code": 200,
                 "url": "test",
                 "text": b"<html><body><a href='test-url'>Known issues</a><a href='test-url'>Resolved issues</a"
                         b"><a href='test-url'>Change log</a></body></html>"})
)
def test_get_bugs_api_missing_timestamp_and_bug_rows(**_kwargs):
    """
    requirement:
                 1. continue bug search even if release notes timestamp is unknown
                 2. raise VendorResponseError if an html element for issues could not be located ( xpaths are dated )
    description: the release notes timestamp could not be located but bug search should resume, if the issues elements
                 cannot be located with configured xpaths, a VendorResponseError should be raised so the xpaths could be
                 inspected and updated by the dev team
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    try:
        FortinetApiClient.get_bugs(
            self=MockFortinetApiClient(),
            release_notes_url="test-url", product_name="Test Product", product_version="1.0.0"
        )
        assert False
    except VendorResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs:
    type("request", (object,),
         {
             "status_code": 200,
             "url": "test",
             "text": b'<html><body><a href="test-url">Known issues</a><a href="test-url">Resolved issues</a>'
                     b'<a href="test-url">Change log</a><div id="content"><h2>Test Category</h2><table><th>Bug ID</th>'
                     b'<tbody><tr></tr><tr></tr></tbody></table></div></body></html>'
         })
)
def test_get_bugs_api_missing_bug_ids(**_kwargs):
    """
    requirement:
                 1. continue bug search even if release notes timestamp is unknown
                 2. raise VendorResponseError if the bugId xpath is not locating bugIds
    description: the release notes timestamp could not be located but bug search should resume, if the bugId xpath is
                 failing, a VendorResponseError should be raised so the xpaths could be inspected and updated by the
                 dev team
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    try:
        FortinetApiClient.get_bugs(
            self=MockFortinetApiClient(),
            release_notes_url="test-url", product_name="Test Product", product_version="1.0.0"
        )
        assert False
    except VendorResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs:
    type("request", (object,),
         {
             "status_code": 200,
             "url": "test",
             "text": b'<html><body><a href="test-url">Known issues</a> <a href="test-url">Resolved issues</a>'
                     b'<a href="test-url">Change log</a><div id="content"><h2>Test Category</h2><table><th>Bug ID</th>'
                     b'<tbody><tr><td>badID</td></tr><tr><td><p>badID</p></td></tr></tbody></table></div></body>'
                     b'</html>'
         })
)
def test_get_bugs_bug_id_format_unknown(**_kwargs):
    """
    requirement:
                 1. continue bug search even if release notes timestamp is unknown
                 2. bug ID is found but the format is unknown
    description: the bug ID format is unknown a VendorResponseError should be raised so the regex could be inspected
                 and updated by the dev team
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    try:
        FortinetApiClient.get_bugs(
            self=MockFortinetApiClient(), release_notes_url="test-url", product_name="Test Product",
            product_version="1.0.0"
        )
        assert False
    except VendorResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request',
    lambda **_kwargs:
    type("request", (object,),
         {
             "status_code": 200,
             "url": "test",
             "text": b'<html><body><a href="test-url">Known issues</a> <a href="test-url">Resolved issues</a>'
                     b'<a href="test-url">Change log</a><div id="content"><h2>Test Category</h2><table><th>Bug ID</th>'
                     b'<tbody><tr><td>666666</td></tr><tr><td><p>6666667</p></td></tr></tbody></table></div></body>'
                     b'</html>'
         })
)
def test_get_bugs_successful(**_kwargs):
    """
    requirement:
                 1. continue bug search even if release notes timestamp is unknown
    description: an html with two issues should return a list of two bugs
    :return:
    """
    from vendor_fortinet_api_client import FortinetApiClient
    bugs = FortinetApiClient.get_bugs(
            self=MockFortinetApiClient(),
            release_notes_url="test-url", product_name="Test Product", product_version="1.0.0"
        )
    assert len(bugs) == 2

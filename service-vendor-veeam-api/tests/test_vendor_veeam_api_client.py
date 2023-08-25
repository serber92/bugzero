"""
unittest for vendor_veeam_api_client
"""
import datetime
import os
from unittest.mock import patch

import pytest

from tests.external_dependencies import mock_env, MockVeeamApiClient, mock_managed_product, mock_database_init, \
    mock_operational_error, mock_formatted_mandatory_fields_missing, mock_formatted_bugs, \
    mock_just_processed_managed_product, mock_old_bugs, mock_how_to_kbs, mock_new_bugs, mock_kb_html, \
    mock_kb_html_missing_description
from vendor_exceptions import ApiConnectionError, ApiResponseError, VendorConnectionError, VendorResponseError


########################################################################################################################
#                                                format_bug_entry                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug",
    [
        (MockVeeamApiClient(), mock_formatted_mandatory_fields_missing[0]),
        (MockVeeamApiClient(), mock_formatted_mandatory_fields_missing[1]),
        (MockVeeamApiClient(), mock_formatted_mandatory_fields_missing[2]),
        (MockVeeamApiClient(), mock_formatted_mandatory_fields_missing[3]),
        (MockVeeamApiClient(), mock_formatted_mandatory_fields_missing[4])
    ]
)
def test_format_bug_entry_missing_mandatory_field(self, single_bug):
    """
    requirement: formatted bugs must have two mandatory fields ["bugId", "description]
    description: bugs missing any mandatory fields should be skipped, the testing case should return an empty list
    mock: bugs, db_client, VeeamApiClient
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    assert not VeeamApiClient.format_bug_entry(
        self=self, kb_entry=single_bug, managed_product=mock_managed_product[0],
    )


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug",
    [
        (MockVeeamApiClient(), mock_formatted_bugs[0]),
        (MockVeeamApiClient(), mock_formatted_bugs[1]),
        (MockVeeamApiClient(), mock_formatted_bugs[2]),
        (MockVeeamApiClient(), mock_formatted_bugs[3]),
        (MockVeeamApiClient(), mock_formatted_bugs[4])
    ]
)
def test_format_bug_successful(self, single_bug):
    """
    requirement: formatted bugs must have two mandatory fields ["bugId", "description]
    description: valid bugs should be processed and return a list with values
    mock: bugs, db_client, VeeamApiClient
    :param self:
    :param single_bug:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    formatted_bug = VeeamApiClient.format_bug_entry(
        self=self, kb_entry=single_bug, managed_product=mock_managed_product[0]
    )
    assert formatted_bug.get("bugId")


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
    from vendor_veeam_api_client import VeeamApiClient
    from db_client import Database

    instance = VeeamApiClient(vendor_id="veeam")
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
    mock: VeeamApiClient, download_instance, sn_sync **_kwargs
    description: the download instance is returned as false and thus the ApiConnectionError is raised
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        VeeamApiClient.sn_sync(
            self=MockVeeamApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
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
    mock: VeeamApiClient, download_instance, sn_sync **_kwargs
    description: JSONDecodeError will re-raise a custom ApiResponseError
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        VeeamApiClient.sn_sync(
            self=MockVeeamApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
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
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        VeeamApiClient.sn_sync(
            self=MockVeeamApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
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
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    instances = VeeamApiClient.sn_sync(
        self=MockVeeamApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
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
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    instances = VeeamApiClient.sn_sync(
        self=MockVeeamApiClient(), query_product=query_product, sn_auth_token="", sn_api_url=""
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
    from vendor_veeam_api_client import VeeamApiClient
    assert VeeamApiClient.timestamp_format(time_str=time_str) == expected_value


########################################################################################################################
#                                                get_kb_article_links                                                  #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 400, "url": "test",  "text": b'{"result": []}'
    })
)
def test_get_kb_article_links_api_connection_error(*_args, **_kwargs):
    """
    requirement: retrieve all kb article for a given product from https://www.veeam.com/services/kb-articles
    mock: requests lib, api response, VeeamApiClient, product
    description: connection error will trigger a ApiConnectionError
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        VeeamApiClient.get_kb_article_links(self=MockVeeamApiClient(), product=query_product)
        assert False
    except ApiConnectionError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test",  "text": b'non json'
    })
)
def test_get_kb_article_links_api_response_error(*_args, **_kwargs):
    """
    requirement: retrieve all kb article for a given product from https://www.veeam.com/services/kb-articles
    mock: requests lib, api response, VeeamApiClient, product
    description: json parse error on the api response will trigger a ApiResponseError
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        VeeamApiClient.get_kb_article_links(self=MockVeeamApiClient(), product=query_product)
        assert False
    except ApiResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test", "text": b'{"result": []}'
    })
)
def test_get_kb_article_links_api_response_missing_field(*_args, **_kwargs):
    """
    requirement: retrieve all kb article for a given product from https://www.veeam.com/services/kb-articles
    mock: requests lib, api response, VeeamApiClient, product
    description: a missing mandatory field in the repo1nse json will trigger  a ApiResponseError
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    try:
        VeeamApiClient.get_kb_article_links(self=MockVeeamApiClient(), product=query_product)
        assert False
    except ApiResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test",
        "text": '{"articles": ' + f"{list(range(10))}" + ', "totalSize": 20}'})
)
def test_get_kb_article_link_pagination(*_args, **_kwargs):
    """
    requirement: retrieve all kb article for a given product from https://www.veeam.com/services/kb-articles
    mock: requests lib, api response, VeeamApiClient, product
    description: setting the pagination limit to 10 out of 20 should still return a total of 20 kb urls
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    query_product = {
        "name": "test product",
        "name_encoded": "test%20product",
        "id": "999",
        "abbr": "tp",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": f"install_status=1^operational_status=1^nameSTARTSWITHtest%20product"
    }
    kb_articles = VeeamApiClient.get_kb_article_links(self=MockVeeamApiClient(), product=query_product)
    assert len(kb_articles) == 20


########################################################################################################################
#                                               crawl_vendor_products                                                  #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 400, "url": "test", "text": ''}
         )
)
def test_crawl_vendor_products_connection_error(*_args, **_kwargs):
    """
    requirement: retrieve all vendor products from https://www.veeam.com/knowledge-base.html
    mock: VeeamApiClient, requests lib, http response
    description: connection error will trigger an VendorConnectionError
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    try:
        VeeamApiClient.crawl_vendor_products(self=MockVeeamApiClient())
        assert False
    except VendorConnectionError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test", "text": '<html><body><div>nothing here</div></body></html>'}
         )
)
def test_crawl_vendor_products_response_error(*_args, **_kwargs):
    """
    requirement: retrieve all vendor products from https://www.veeam.com/knowledge-base.html
    mock: VeeamApiClient, requests lib, http response
    description: missing mandatory html element  will trigger a VendorResponseError
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    try:
        VeeamApiClient.crawl_vendor_products(self=MockVeeamApiClient())
        assert False
    except VendorResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.request', lambda **_kwargs:
    type("request", (object,), {
        "status_code": 200, "url": "test",
        "text": '<html><body><select name="product"><option value="prod_1">product_1</option></select></body></html>'}
         )
)
def test_crawl_vendor_products(*_args, **_kwargs):
    """
    requirement: retrieve all vendor products from https://www.veeam.com/knowledge-base.html
    mock: VeeamApiClient, requests lib, http response
    description: a non empty list of product should be returned
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    vendor_products = VeeamApiClient.crawl_vendor_products(self=MockVeeamApiClient())
    assert isinstance(vendor_products, list) and vendor_products


########################################################################################################################
#                                              filter_bugs                                                             #
########################################################################################################################
def test_filter_bugs_old_bugs(*_args, **_kwargs):
    """
    requirement: filter and format bugs
    mock: bugs, bugs_days_back, VeeamApiClient, managed_product
    description: filter out old bugs ( older than bugs_days_back ) return an emtpy list
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    filtered_bugs = VeeamApiClient.filter_bugs(
        self=MockVeeamApiClient(), managed_product=mock_just_processed_managed_product[0], bugs=mock_old_bugs,
        bugs_days_back=100)
    assert isinstance(filtered_bugs, list) and not filtered_bugs


def test_filter_bugs_general_bugs(*_args, **_kwargs):
    """
    requirement: filter and format bugs
    mock: bugs, bugs_days_back, VeeamApiClient, managed_product
    description: filter out general bugs ( bug summary field included blacklisted kw ) return an emtpy list
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    filtered_bugs = VeeamApiClient.filter_bugs(
        self=MockVeeamApiClient(), managed_product=mock_just_processed_managed_product[0], bugs=mock_how_to_kbs,
        bugs_days_back=100)
    assert isinstance(filtered_bugs, list) and not filtered_bugs


def test_filter_bugs(*_args, **_kwargs):
    """
    requirement: filter and format bugs
    mock: bugs, bugs_days_back, VeeamApiClient, managed_product
    description: verified bugs should be returned in a list
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    filtered_bugs = VeeamApiClient.filter_bugs(
        self=MockVeeamApiClient(), managed_product=mock_just_processed_managed_product[0], bugs=mock_new_bugs,
        bugs_days_back=100)
    assert isinstance(filtered_bugs, list) and filtered_bugs


########################################################################################################################
#                                              parse_kb_html                                                           #
########################################################################################################################
def test_parse_kb_html_missing_mandatory_field(*_args, **_kwargs):
    """
    requirement: parse bug data fields from a kb html page
    mock: kb entry, kb html, VeeamApiClient, managed_product
    description: return false if mandatory field is missing update kb_info_parse_errors
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    kb = {
        "id": "kb4234",
        "title": "Veeam ONE version 10/10a impact on VMware vSAN",
        "product": [
            {
                "name": "Veeam ONE",
                "version": 116,
                "versionName": "Veeam ONE 10"
            }
        ],
        "type": "article",
        "url": "/kb4234",
        "date": "2/11/2021",
        "newsletterDate": "2/11/2021"
    }
    kb_data = VeeamApiClient.parse_kb_html(
        self=MockVeeamApiClient(), managed_product=mock_just_processed_managed_product[0], kb=kb,
        html=mock_kb_html_missing_description
    )
    assert not kb_data


def test_parse_kb_html(*_args, **_kwargs):
    """
    requirement: parse bug data fields from a kb html page
    mock: kb entry, kb html, VeeamApiClient, managed_product
    description: return enriched kb entry with existing mandatory fields
    :param _args:
    :param _kwargs:
    :return:
    """
    from vendor_veeam_api_client import VeeamApiClient
    kb = {
             "id": "kb4234",
             "title": "Veeam ONE version 10/10a impact on VMware vSAN",
             "product": [
                 {
                     "name": "Veeam ONE",
                     "version": 116,
                     "versionName": "Veeam ONE 10"
                 }
             ],
             "type": "article",
             "url": "/kb4234",
             "date": "2/11/2021",
             "newsletterDate": "2/11/2021"
         }
    kb_data = VeeamApiClient.parse_kb_html(
        self=MockVeeamApiClient(), managed_product=mock_just_processed_managed_product[0], kb=kb, html=mock_kb_html)
    assert kb_data.get("description", None)

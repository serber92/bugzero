"""
unit testing for vendor_msft_bug_service
"""
import datetime
import os
import sys
from unittest.mock import patch

import pytest
from vendor_msft_supported_products import sql_server_products

from tests.external_dependencies import mock_env, MockDbClientExistingServiceEntry, mock_sql_bugs, MockQueueManager, \
    MockQueueObject, MockSecretManagerClient, mock_request_session_w_auth_tokens, \
    mock_to_execute_sql_server_managed_product, cu_kb_html_example, cu_kb_html_example_no_bug_ids, \
    cu_kb_html_example_invalid_bug_ids, cu_build_html_example, mock_request_session_missing_auth_tokens
from vendor_exceptions import ApiConnectionError, ApiResponseError, VendorResponseError, VendorConnectionError


########################################################################################################################
#                                                timestamp_format                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "time_str, expected_value",
    [
        ("2021-04-22T22:20:22Z",
         datetime.datetime.strptime("2021-04-22T22:20:22Z", "%Y-%m-%dT%H:%M:%SZ")),
        ("2021-05-22T22:20:22.000001Z",
         datetime.datetime.strptime("2021-05-22T22:20:22", "%Y-%m-%dT%H:%M:%S")),
        ("August 10,2021",
         datetime.datetime.strptime("August 10,2021", "%B %d,%Y")),
        ("bad-string", None)
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
    from vendor_msft_api_client import MsftApiClient
    assert MsftApiClient.timestamp_format(time_str=time_str) == expected_value


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
    from vendor_msft_api_client import MsftApiClient
    instance = MsftApiClient(vendor_id="msft")
    assert not instance.bug_zero_vendor_status_update(
        db_client=MockDbClientExistingServiceEntry, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )


@patch.dict(os.environ, mock_env())
def test_bug_zero_vendor_status_update_new_entry(*_args):
    """
    requirement: execute bug_zero_vendor_status_update successfully
    mock: db_client, **kwargs for bug_zero_vendor_status_update
    description: a successful execution should complete without raising errors and no values return
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    instance = MsftApiClient(vendor_id="msft")
    assert not instance.bug_zero_vendor_status_update(
        db_client=MockDbClientExistingServiceEntry, started_at="", services_table="services",
        service_execution_table="serviceExecution", service_status="", vendor_id="", service_id="",
        service_name="", error=0, message=""
    )


########################################################################################################################
#                                               consolidate_bugs                                                       #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('vendor_msft_api_client.MsftApiClient.bug_kbs_crawling_manager')
def test_consolidate_bugs_no_bugs(*_args, **_kwargs):
    """
    requirement: when on or more bugs with the same id ( bug was retrieved from more than one product release notes ),
                 the entries should be consolidated and include both products under bug["knownFixedReleases"]
    description: two bug entries with the sam bugId should be consolidated and the bug["knownFixedReleases"] should
                 include 2 products
    mock: db_client, MsftApiClient, bugs
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    MsftApiClient.consolidate_bugs(self=self, vendor_id="msft", bugs=mock_sql_bugs)
    assert len(self.formatted_bugs[0]["knownFixedReleases"].split(",")) == 2


########################################################################################################################
#                                               crawl_bug_kbs                                                          #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_crawl_bug_kbs_non_kb_bug(*_args, **_kwargs):
    """
    requirement: crawl_bug_kbs retrieves data from a kb document page, if the bug['hasKb'] is false the crawl will not
                 start and the bug will be saved as is
    description: a bug with 'hasKb': False is not processed and the function should complete and the bug should be added
                 to the instance kb_bugs
    mock: db_client, MsftApiClient, bugs
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"hasKb": False, "id": 1}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_bug_kbs(self=self, q=queue_object, product_name="test")
    assert self.kb_bugs[0]['id'] == 1


@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 401, "url": "test"}))
@patch.dict(os.environ, mock_env())
def test_crawl_bug_kbs_response_error(*_args, **_kwargs):
    """
    requirement: crawl_bug_kbs retrieves data from a kb document page, if the download fails the bug will be saved as is
    description: failed request the download the kb page is not processed and the function should complete and the bug
                 should be added to the instance kb_bugs
    mock: db_client, MsftApiClient, failed response from server
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"hasKb": True, "id": 1, "bugUrl": "test"}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_bug_kbs(self=self, q=queue_object, product_name="test")
    assert self.kb_bugs[0]['id'] == 1


@patch('requests.get',
       lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test", "text": "<html></html>"})
       )
@patch.dict(os.environ, mock_env())
def test_crawl_bug_kbs_missing_bug_id(*_args, **_kwargs):
    """
    requirement: crawl_bug_kbs retrieves data from a kb document page, if the original bug entry does no include a
                 bugId, it is retrieved from the downloaded kb page and if failed, the bug will be skipped
    description: failure to parse the bug id from the donwloaded page results in skipping the bug, kb_bugs will be empty
    mock: db_client, MsftApiClient, html string with missing bugId
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"hasKb": True, "id": 1, "bugUrl": "test", "bugId": ""}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_bug_kbs(self=self, q=queue_object, product_name="test")
    assert not self.kb_bugs


@patch('requests.get',
       lambda **_kwargs: type("request", (object,),
                              {"status_code": 200, "url": "test",
                               "text": "<html><meta name='awa-asst' content='test'></meta></html>"}
                              )
       )
@patch.dict(os.environ, mock_env())
def test_crawl_bug_kbs_missing_kb_content(*_args, **_kwargs):
    """
    requirement: crawl_bug_kbs retrieves data from a kb document page, if kb_content could not be retrieved, the parsing
                 process stops and the bug is added as if missing a few fields
    description: failure to kb_content from the downloaded page will results in an empty description field
    mock: db_client, MsftApiClient, html string with missing kb content
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"hasKb": True, "id": 1, "bugUrl": "test", "bugId": ""}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_bug_kbs(self=self, q=queue_object, product_name="test")
    assert not self.kb_bugs[0].get('description')


@patch('requests.get',
       lambda **_kwargs:
       type("request", (object,),
            {
                "status_code": 200, "url": "test",
                "text": "<html>"
                        "<meta name='awa-asst' content='test'></meta>"
                        "<meta name='lastPublishedDate' content='2021-01-01'></meta>"
                        "<meta name='firstPublishedDate' content='2021-01-01'></meta>"
                        "<main id='main'></main></html>"
            }
            )
       )
@patch.dict(os.environ, mock_env())
def test_crawl_bug_kbs(*_args, **_kwargs):
    """
    requirement: a successful crawl and parse of the kb_data
    description: the bug entry should have a populated vendorCreatedDate field
    mock: db_client, MsftApiClient, failed response from server
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"hasKb": True, "id": 1, "bugUrl": "test", "bugId": ""}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_bug_kbs(self=self, q=queue_object, product_name="test")
    assert self.kb_bugs[0].get('vendorLastUpdatedDate')


########################################################################################################################
#                                               crawl_cu_kbs                                                          #
########################################################################################################################
@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 401, "url": "test"}))
@patch.dict(os.environ, mock_env())
def test_crawl_cu_kbs_response_error(*_args, **_kwargs):
    """
    requirement: crawl cumulative update pages and parse the release bugs from the html string, if the the page fails to
                 to download return false
    description: a connection error result in the download error an a false return from the function, the instance's
                 pre_formatted_sql_bugs variable used to store processed bugs will be empty
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"kb": {"kb_url": "test", "kb_id": 1}, "id": 1}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_cu_kbs(
        self=self, q=queue_object, managed_product=mock_to_execute_sql_server_managed_product[0], service_now_table=""
    )
    assert not self.pre_formatted_sql_bugs


@patch('requests.get',
       lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test", "text": "<html></html>"})
       )
@patch.dict(os.environ, mock_env())
def test_crawl_cu_kbs_missing_bug_rows(*_args, **_kwargs):
    """
    requirement: crawl cumulative update pages and parse the release bugs from the html string, if the parser can't
                 locate the bug rows elements with the provided xpaths, the process will stop and
                 function the function will return false
    description: failure to locate the bug rows using xpaths terminates the process and return false , the instance's
                 pre_formatted_sql_bugs variable used to store processed bugs will be empty
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"kb": {"kb_url": "test", "kb_id": 1}, "id": 1}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_cu_kbs(
        self=self, q=queue_object, managed_product=mock_to_execute_sql_server_managed_product[0], service_now_table=""
    )
    assert not self.pre_formatted_sql_bugs


@patch('requests.get',
       lambda **_kwargs:
       type(
           "request", (object,),
           {
               "status_code": 200,
               "url": "test",
               "text": f"<html>{cu_kb_html_example_no_bug_ids}</html>"}
       )
       )
@patch.dict(os.environ, mock_env())
def test_crawl_cu_kbs_bug_ids_missing(*_args, **_kwargs):
    """
    requirement: crawl cumulative update pages and parse the release bugs from the html string, if the parser can't
                 locate the bug ids for each bug the function will return false
    description: failure to locate the bug ids for all the bug rows using xpaths terminates the process and return false
                 the instance's pre_formatted_sql_bugs variable used to store processed bugs will be empty
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"kb": {"kb_url": "test", "kb_id": 1}, "id": 1}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_cu_kbs(
        self=self, q=queue_object, managed_product=mock_to_execute_sql_server_managed_product[0], service_now_table=""
    )
    assert not self.pre_formatted_sql_bugs


@patch('requests.get',
       lambda **_kwargs:
       type(
           "request", (object,),
           {
               "status_code": 200,
               "url": "test",
               "text": f"<html>{cu_kb_html_example_invalid_bug_ids}</html>"}
       )
       )
@patch.dict(os.environ, mock_env())
def test_crawl_cu_kbs_invalid_bug_ids(*_args, **_kwargs):
    """
    requirement: crawl cumulative update pages and parse the release bugs from the html string, if the parser can't
                 convert the bugId to int, the bug is skipped
    description: failure to convert the bug ids for all the bug rows, the instance's pre_formatted_sql_bugs variable
                 used to store processed bugs will be empty
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {"kb": {"kb_url": "test", "kb_id": 1}, "id": 1}
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_cu_kbs(
        self=self, q=queue_object, managed_product=mock_to_execute_sql_server_managed_product[0], service_now_table=""
    )
    assert not self.pre_formatted_sql_bugs


@patch('requests.get',
       lambda **_kwargs:
       type("request", (object,), {"status_code": 200, "url": "test", "text": f"<html>{cu_kb_html_example}</html>"})
       )
@patch.dict(os.environ, mock_env())
def test_crawl_cu_kbs(*_args, **_kwargs):
    """
    requirement: crawl cumulative update pages and parse the release bugs from the html string
    description: a successful process should results in the instance's pre_formatted_sql_bugs variable
                 used to store processed bugs having entries
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    bug = {
        "kb": {"kb_url": "test", "kb_id": 1, "build_version": "", "build_name": "", "build_version_number": "",
               "release_date": "", "": ""},
        "id": 1, "affected_ci": []
    }
    queue_object = MockQueueObject(entry=bug)
    MsftApiClient.crawl_cu_kbs(
        self=self, q=queue_object, managed_product=mock_to_execute_sql_server_managed_product[0], service_now_table=""
    )
    assert self.pre_formatted_sql_bugs


########################################################################################################################
#                                               parse_cu_releases                                                      #
########################################################################################################################
@patch('requests.get', lambda **_kwargs:
       type("request", (object,), {"status_code": 200, "url": "test", "text": f"<html>{cu_kb_html_example}</html>"})
       )
@patch.dict(os.environ, mock_env())
def test_parse_cu_releases_missing_release_date(*_args, **_kwargs):
    """
    requirement: crawl release build pages, parse release rows and get all the data necessary to build the kb entry, if
                 a kb release date parse fails, a VendorResponseError is raised
    description: wrong xpath to get a kb release date triggers VendorResponseError
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    product = {
        "id": "SQL Server 2019",
        "name": "SQL Server 2019",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH15.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/kb4518398-sql-server-2019-build-versions-"
            "782ed548-1cd8-b5c3-a566-8b4f9e20293a"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build": "./td[2]/p/text()",
            "kb_url": "./td[6]/p/a/@href",
            "kb_id": "./td[6]/p/a/text()",
            "build_name": "./td[1]/p/text()",
            "release_date": './td[last()]/h7/text()'
        }
    }
    response = type("request", (object,),
                    {"status_code": 200, "url": "test", "text": cu_build_html_example}
                    )
    try:
        MsftApiClient.parse_cu_releases(
            self=self, product=product, source_url="", bugs_days_back_date=datetime.datetime(2021, 1, 1),
            html_string=response
        )
        assert False
    except VendorResponseError:
        assert True


@patch('requests.get', lambda **_kwargs:
       type("request", (object,), {"status_code": 200, "url": "test", "text": f"<html>{cu_kb_html_example}</html>"})
       )
@patch.dict(os.environ, mock_env())
def test_parse_cu_releases_missing_build_version(*_args, **_kwargs):
    """
    requirement: crawl release build pages, parse release rows and get all the data necessary to build the kb entry, if
                 a kb build version parse fails the kb row is skipped
    description: wrong xpath to get a kb build version fails and all kb release are skipped, out_of_scope_releases and
                 inside_scope_releases lists are empty
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    product = {
        "id": "SQL Server 2019",
        "name": "SQL Server 2019",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH15.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/kb4518398-sql-server-2019-build-versions-"
            "782ed548-1cd8-b5c3-a566-8b4f9e20293a"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build": "./td[2]/p/h7/text()",
            "kb_url": "./td[6]/p/a/@href",
            "kb_id": "./td[6]/p/a/text()",
            "build_name": "./td[1]/p/text()",
            "release_date": './td[last()]/p/text()'
        }
    }
    response = type("request", (object,),
                    {"status_code": 200, "url": "test", "text": cu_build_html_example}
                    )
    out_of_scope_releases, _cumulative_update_kbs, _inside_scope_releases = MsftApiClient.parse_cu_releases(
        self=self, product=product, source_url="", bugs_days_back_date=datetime.datetime(2021, 1, 1),
        html_string=response
        )
    assert not out_of_scope_releases


@patch(
    'requests.get', lambda **_kwargs:
    type("request", (object,), {"status_code": 200, "url": "test", "text": f"<html>{cu_kb_html_example}</html>"})
       )
@patch.dict(os.environ, mock_env())
def test_parse_cu_releases_out_of_scope(*_args, **_kwargs):
    """
    requirement: if a kb release entry has a release date older than the bugs_days_back_date, it is ignored
    description: all the kb release entries are out of scope and the out_of_scope_releases list has entries and
                 inside_scope_releases list is empty
    mock: db_client, MsftApiClient, requests.get
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    product = {
        "id": "SQL Server 2019",
        "name": "SQL Server 2019",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH15.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/kb4518398-sql-server-2019-build-versions-"
            "782ed548-1cd8-b5c3-a566-8b4f9e20293a"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build": "./td[2]/p/text()",
            "kb_url": "./td[6]/p/a/@href",
            "kb_id": "./td[6]/p/a/text()",
            "build_name": "./td[1]/p/text()",
            "release_date": './td[last()]/p/text()'
        }
    }
    response = type("request", (object,),
                    {"status_code": 200, "url": "test", "text": cu_build_html_example}
                    )
    out_of_scope_releases, _cumulative_update_kbs, inside_scope_releases = MsftApiClient.parse_cu_releases(
        self=self, product=product, source_url="", bugs_days_back_date=datetime.datetime.now(),
        html_string=response
    )
    assert out_of_scope_releases and not inside_scope_releases


########################################################################################################################
#                                                     sn_sync                                                          #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
def test_sn_sync_api_connection_error(*_args, **_kwargs):
    """
    requirement: query SN for affected CIs
    description: a download error resulting in an ApiConnectionError exception
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    query_product = {"snCiFilter": "test", "service_now_table": "test", "sysparm_query": ""}
    try:
        MsftApiClient.sn_sync(
            self=self, sn_api_url="", sn_auth_token="", affected_ci_query_base="", product=query_product
        )
        assert False
    except ApiConnectionError:
        assert True


@patch.dict(os.environ, mock_env())
@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 200, "headers": {}}))
def test_sn_sync_api_response_error(*_args, **_kwargs):
    """
    requirement: query SN for affected CIs
    description: missing x-total-count header from response resulting in an ApiResponseError exception
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    query_product = {"snCiFilter": "test", "service_now_table": "test", "sysparm_query": ""}
    try:
        MsftApiClient.sn_sync(
            self=self, sn_api_url="", sn_auth_token="", product=query_product, affected_ci_query_base=""
        )
        assert False
    except ApiResponseError:
        assert True


@patch.dict(os.environ, mock_env())
@patch(
    'requests.get', lambda **_kwargs:
    type("request", (object,), {"status_code": 200, "headers": {"x-total-count": 1}, "text": '{"result": true}'})
)
def test_sn_sync_success(*_args, **_kwargs):
    """
    requirement: query SN for affected CIs
    description: successful execution resulting in a True value
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient()
    query_product = {"snCiFilter": "test", "service_now_table": "test", "sysparm_query": "", "name": "test"}
    execution = MsftApiClient.sn_sync(self=self, sn_api_url="", sn_auth_token="", product=query_product,
                                      affected_ci_query_base="")
    assert execution


########################################################################################################################
#                                               get_aws_secret_value                                                   #
########################################################################################################################
def test_get_aws_secret_value_success(*_args):
    """
    requirement: return secret value from AWS SecretManager
    mock: Aws SecretManager client, MsftApiClient
    description: return secret value
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    assert MsftApiClient.get_aws_secret_value(
        MockSecretManagerClient(secret_binary=True, secret_string=True), secret_name=True,
        mandatory_fields=["setting-msft365-admin"]
    )
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


def test_get_aws_secret_value_missing_field(*_args):
    """
    requirement: return secret value from AWS SecretManager
    mock: Aws SecretManager client, MsftApiClient
    description: if a mandatory field is missing ApiConnectionError is raised
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    try:
        MsftApiClient.get_aws_secret_value(
            MockSecretManagerClient(secret_binary=True, secret_string=True), secret_name=True,
            mandatory_fields=["missing_field"]
        )
        assert False
    except ApiConnectionError:
        assert True

    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


########################################################################################################################
#                                               gen_admin_dashboard_tokens                                             #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch(
    'vendor_msft_api_client.MsftApiClient.process_login_step',
    lambda *args, **kwargs: [{}, mock_request_session_missing_auth_tokens]
)
def test_gen_admin_dashboard_tokens_login_error(*_args):
    """
    requirement: follow a login sequence and return cookies with access microsoft Admin Dashboard access tokens, if the
                 tokens are not found a ApiResponseError is raised
    mock: MsftApiClient, session cookies
    description: missing tokens in session cookies at the end of the process raise an ApiResponseError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    try:
        MsftApiClient.gen_admin_dashboard_tokens(self=self, username="test", password="test")
        assert False
    except ApiResponseError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'vendor_msft_api_client.MsftApiClient.process_login_step',
    lambda *args, **kwargs: [{}, mock_request_session_w_auth_tokens]
)
def test_gen_admin_dashboard_tokens(*_args):
    """
    requirement: follow a login sequence and return cookies with access microsoft Admin Dashboard access tokens
    mock: MsftApiClient, session cookies
    description: successful login return access cookies
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    cookies = MsftApiClient.gen_admin_dashboard_tokens(self=self, username="test", password="test")
    assert cookies
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


########################################################################################################################
#                                                process_login_step                                                   #
########################################################################################################################
@patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 401, "url": "test"}))
@patch.dict(os.environ, mock_env())
def test_process_login_step_post_json_step_error(*_args):
    """
    requirement: process a post method login step with a json form, if the request fails and the response object is
                 false, raise an ApiConnectionError
    mock: MsftApiClient, session, step data
    description: false response object will raise an ApiConnectionError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
               "url": "https://www.test.com", "parse_json": True,
               "parse_regex": False, "regex_string": r'',
               "log_message": "getting login credentials cookies",
               "error_message": "admin dashboard credentials cookie parse failed",
               "post": True, "post_form": {}, "form": {}, "form_fields_map": ['flowToken'],
               "store_fields": {"flowToken": "FlowToken"}, 'xpaths': [],
               "json_form": True, "parse_html": False
    }
    stored_data = {"flowToken": ""}
    session = {}
    try:
        MsftApiClient.process_login_step(
            self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
        )
        assert False
    except ApiConnectionError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 401, "url": "test"}))
@patch.dict(os.environ, mock_env())
def test_process_login_step_post_step_error(*_args):
    """
    requirement: process a post method login step with a x-www form , if the request fails and the response object is
                 false, raise an ApiConnectionError
    mock: MsftApiClient, session, step data
    description: false response object will raise an ApiConnectionError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
        "url": "https://www.test.com", "parse_json": True,
        "parse_regex": False, "regex_string": r'',
        "log_message": "getting login credentials cookies",
        "error_message": "admin dashboard credentials cookie parse failed",
        "post": True, "post_form": {}, "form": {}, "form_fields_map": ['flowToken'],
        "store_fields": {"flowToken": "FlowToken"}, 'xpaths': [],
        "json_form": False, "parse_html": False
    }
    stored_data = {"flowToken": ""}
    session = {}
    try:
        MsftApiClient.process_login_step(
            self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
        )
        assert False
    except ApiConnectionError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 401, "url": "test"}))
@patch.dict(os.environ, mock_env())
def test_process_login_step_get_step_error(*_args):
    """
    requirement: process a get method login step with, if the request fails and the response object is
                 false, raise an ApiConnectionError
    mock: MsftApiClient, session, step data
    description: false response object will raise an ApiConnectionError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
        "url": "https://www.test.com", "parse_json": False,
        "parse_regex": False, "regex_string": r'',
        "log_message": "getting login credentials cookies",
        "error_message": "admin dashboard credentials cookie parse failed",
        "post": False, "post_form": {}, "form": {}, "form_fields_map": [],
        "store_fields": {"flowToken": "FlowToken"}, 'xpaths': [],
        "json_form": False, "parse_html": False
    }
    stored_data = {"flowToken": ""}
    session = {}
    try:
        MsftApiClient.process_login_step(
            self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
        )
        assert False
    except ApiConnectionError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch(
    'requests.get', lambda **_kwargs: type("request", (object,),
                                           {"status_code": 200, "url": "test", "text": "invalid text"})
)
@patch.dict(os.environ, mock_env())
def test_process_login_step_get_step_parse_regex_error(*_args):
    """
    requirement: process a get method login step with, using a regex parser on the response.text if the steps requires,
                 if the parsing fails, an ApiResponseError is raised
    mock: MsftApiClient, session, step data
    description: bad response.text will raise an ApiResponseError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
        "url": "https://www.test.com", "parse_json": True,
        "parse_regex": True, "regex_string": r'(?<=)text to find(?=end of text)',
        "log_message": "getting login credentials cookies",
        "error_message": "admin dashboard credentials cookie parse failed",
        "post": False, "post_form": {}, "form": {}, "form_fields_map": [],
        "store_fields": {"flowToken": "FlowToken"}, 'xpaths': [],
        "json_form": False, "parse_html": False
    }
    stored_data = {"flowToken": ""}
    session = {}
    try:
        MsftApiClient.process_login_step(
            self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
        )
        assert False
    except ApiResponseError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch(
    'requests.get', lambda **_kwargs: type("request", (object,),
                                           {"status_code": 200, "url": "test", "text": "invalid text"})
)
@patch.dict(os.environ, mock_env())
def test_process_login_step_get_step_decode_json_error(*_args):
    """
    requirement: process a get method login step with, load the text as json if the steps requires,
                 if the decoding fails, an ApiResponseError is raised
    mock: MsftApiClient, session, step data
    description: bad response.text will raise an ApiResponseError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
        "url": "https://www.test.com", "parse_json": True,
        "parse_regex": False, "regex_string": r'',
        "log_message": "getting login credentials cookies",
        "error_message": "admin dashboard credentials cookie parse failed",
        "post": False, "post_form": {}, "form": {}, "form_fields_map": [],
        "store_fields": {"flowToken": "FlowToken"}, 'xpaths': [],
        "json_form": False, "parse_html": False
    }
    stored_data = {"flowToken": ""}
    session = {}
    try:
        MsftApiClient.process_login_step(
            self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
        )
        assert False
    except ApiResponseError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch(
    'requests.get', lambda **_kwargs: type("request", (object,),
                                           {"status_code": 200, "url": "test", "text": '{"FlowToken": "test"}'})
)
@patch.dict(os.environ, mock_env())
def test_process_login_step_get_json(*_args):
    """
    requirement: process a get method login step with, load the text as json if the steps requires,
                 store the required fields specified in store_fields
    mock: MsftApiClient, session, step data
    description: successful json step results in storing the required store_fields
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
        "url": "https://www.test.com", "parse_json": True,
        "parse_regex": False, "regex_string": r'',
        "log_message": "getting login credentials cookies",
        "error_message": "admin dashboard credentials cookie parse failed",
        "post": False, "post_form": {}, "form": {}, "form_fields_map": [],
        "store_fields":  {"flowToken": "FlowToken"}, 'xpaths': [],
        "json_form": False, "parse_html": False
    }
    stored_data = {}
    session = {}
    stored_data, _session = MsftApiClient.process_login_step(
        self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
    )
    assert stored_data

    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch(
    'requests.get', lambda **_kwargs:
    type("request", (object,),
         {"status_code": 200, "url": "test", "text": '<html><input name="id_token" value="test"></input></html>'}
         )
)
@patch.dict(os.environ, mock_env())
def test_process_login_step_get_parse_html(*_args):
    """
    requirement: process a get method login step with, load the text to an lxml object if the steps requires,
                 store the required fields specified in store_fields
    mock: MsftApiClient, session, step data
    description: successful step results in storing the required store_fields
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    step = {
        "url": "https://www.test.com", "parse_json": False,
        "parse_regex": False, "regex_string": r'',
        "log_message": "getting login credentials cookies",
        "error_message": "admin dashboard credentials cookie parse failed",
        "post": False, "post_form": {}, "form": {}, "form_fields_map": [],
        "store_fields":  {"flowToken": "FlowToken"}, "json_form": False, "parse_html": True,
        'xpaths': [{"xpath": "//input[@name='id_token']/@value", "title": "id_token"}]
    }
    stored_data = {}
    session = {}
    stored_data, _session = MsftApiClient.process_login_step(
        self=self, step_count=1, step_id=1, stored_data=stored_data, step=step, session=session
    )
    assert stored_data

    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


########################################################################################################################
#                                                get_sql_release_bugs                                                  #
########################################################################################################################
@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 401, "url": "test"}))
@patch.dict(os.environ, mock_env())
def test_get_sql_release_bugs_connection_error(*_args):
    """
    requirement: retrieve build description pages and send to the parsing method, if the the page download fails
                 raise an ApiConnectionError
    mock: MsftApiClient, active_cis data, managed_product
    description: false response object will raise an ApiConnectionError
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    managed_product = type("mockManagedProduct", (object,), {"name": "test"})
    try:
        MsftApiClient.get_sql_release_bugs(
            self=self, product=sql_server_products[0], managed_product=managed_product, active_cis=[], bugs_days_back=1
        )
        assert False
    except VendorConnectionError:
        assert True
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_msft_api_client']


@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test"}))
@patch(
    'vendor_msft_api_client.MsftApiClient.parse_cu_releases', lambda *args, **kwargs: [[], [], []]
)
@patch.dict(os.environ, mock_env())
def test_get_sql_release_bugs_no_kbs_found(*_args):
    """
    requirement: retrieve build description pages and send to the parsing method, if none of the parsed kb are
                 compatible with filter conditions an empty list is returned
    mock: MsftApiClient, active_cis data, managed_product
    description: none of the parsed kb are compatible with filter conditions and an empty list is returned
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    managed_product = type("mockManagedProduct", (object,), {"name": "test"})
    assert not MsftApiClient.get_sql_release_bugs(
        self=self, product=sql_server_products[0], managed_product=managed_product, active_cis=[], bugs_days_back=1
    )

    del sys.modules['vendor_msft_api_client']


@patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test"}))
@patch(
    'vendor_msft_api_client.MsftApiClient.parse_cu_releases',
    lambda *args, **kwargs: [[], [{"build_version_number": 2, "build_version": 2, "kb_id": "test"}], []]
)
@patch(
    'vendor_msft_api_client.MsftApiClient.crawl_cu_kbs',
    lambda *args, **kwargs: True
)
@patch(
    'queue.Queue', MockQueueManager
)
@patch.dict(os.environ, mock_env())
def test_get_sql_release_bugs_kbs(*_args):
    """
    requirement: retrieve build description pages and send to the parsing method, if the parsed kb are
                 compatible with the filter conditions the process should complete
    mock: MsftApiClient, active_cis data, managed_product
    description: kb release matching the filtering conditions and the managedProduct
    :return:
    """
    from vendor_msft_api_client import MsftApiClient
    self = MsftApiClient(vendor_id="msft")
    managed_product = type("mockManagedProduct", (object,), {"name": "test"})
    active_cis = [{"version": "1", "sys_id": "test"}]
    assert not MsftApiClient.get_sql_release_bugs(
        self=self, product=sql_server_products[0], managed_product=managed_product, active_cis=active_cis,
        bugs_days_back=1, threads=1
    )

    del sys.modules['vendor_msft_api_client']

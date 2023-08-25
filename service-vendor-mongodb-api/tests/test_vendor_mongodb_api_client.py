"""
unit test fro vendor_mongodb_bug_service
"""
import datetime
import os
import sys
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from tests.external_dependencies import MockMongoApiClient, MockDbClient, mock_env, vmware_bugs_w_versions_examples, \
    vmware_bugs_w_comments_examples, vmware_bugs_w_missing_optional_fields, mock_operational_error, \
    filter_map_example_1, filter_map_example_2, filter_map_example_3, jql_query_1, jql_query_2, jql_query_3


########################################################################################################################
#                                                format_bug_entry                                                      #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug, managed_product_id, empty_list",
    [
        (MockMongoApiClient(), vmware_bugs_w_versions_examples[0], 1, []),
        (MockMongoApiClient(), vmware_bugs_w_versions_examples[1], 1, []),
        (MockMongoApiClient(), vmware_bugs_w_versions_examples[2], 1, []),
        (MockMongoApiClient(), vmware_bugs_w_versions_examples[3], 1, []),
        (MockMongoApiClient(), vmware_bugs_w_versions_examples[4], 1, []),
    ]
)
def test_format_bug_entry_no_version(self, single_bug, managed_product_id, empty_list):
    """
    requirement: retrieved bugs should have values in the 'version' field so it could be attached to a snCI
    mock: bug examples with empty version field
    description: trying to format bugs with empty 'version' field should return an empty list
    :param self:
    :param single_bug:
    :param managed_product_id:
    :param empty_list:
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    assert MongoApiClient.format_bug_entry(
        self=self, bugs=single_bug, managed_product_id=managed_product_id
    ) == empty_list
    # remove mocks import to prevent interference with other tests
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug, managed_product_id, expected_included_string",
    [
        (MockMongoApiClient(), vmware_bugs_w_comments_examples[0], 1, 'Author:'),
        (MockMongoApiClient(), vmware_bugs_w_comments_examples[1], 1, 'Author:'),
        (MockMongoApiClient(), vmware_bugs_w_comments_examples[2], 1, 'Author:'),
        (MockMongoApiClient(), vmware_bugs_w_comments_examples[3], 1, 'Author:'),
        (MockMongoApiClient(), vmware_bugs_w_comments_examples[4], 1, 'Author:'),
    ]
)
def test_format_bug_entry_w_comments(self, single_bug, managed_product_id, expected_included_string):
    """
    requirement: comments should be concatenated with the description field
    mock: bug examples with comments
    description: the description field should include the string 'Author:' indicating the inclusion of comments
    :param self:
    :param single_bug:
    :param managed_product_id:
    :param expected_included_string:
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    assert expected_included_string in MongoApiClient.format_bug_entry(
               self=self, bugs=single_bug, managed_product_id=managed_product_id
           )[0]["description"]
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "self, single_bug, managed_product_id, optional_field",
    [
        (MockMongoApiClient(), vmware_bugs_w_missing_optional_fields[0], 1, 'resolution'),
        (MockMongoApiClient(), vmware_bugs_w_missing_optional_fields[1], 1, 'description'),
        (MockMongoApiClient(), vmware_bugs_w_missing_optional_fields[2], 1, 'fixVersion'),
        (MockMongoApiClient(), vmware_bugs_w_missing_optional_fields[3], 1, 'views'),
        (MockMongoApiClient(), vmware_bugs_w_missing_optional_fields[4], 1, 'votes'),
    ]
)
def test_format_bug_entry_w_missing_optional_fields(self, single_bug, managed_product_id, optional_field):
    """
    requirement: optional bug fields should be empty in the formatted entry if does not exist in the original bug
    mock: bug examples with missing random optional fields
    description: the expected optional field should be empty or non-existing in the formatted entry
    :param self:
    :param single_bug:
    :param managed_product_id:
    :param optional_field:
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    assert MongoApiClient.format_bug_entry(
               self=self, bugs=single_bug, managed_product_id=managed_product_id
           )[0].get(optional_field, "") is ""
    del sys.modules['vendor_mongodb_api_client']


########################################################################################################################
#                                                get_bugs                                                              #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_get_bugs_connection_error(**_kwargs):
    """
    requirement: if MongoDB Jira API request fails,
    ConnectionError("Vendor integration error - MongoDB data APIs are not working properly") should be raised
    mock: MongoApiClient
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    try:
        MongoApiClient.get_bugs(self=MockMongoApiClient(), jql_statement="test-query")
        assert False
    except ConnectionError:
        assert True
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@patch('download_manager.download_instance', lambda **kwargs: type('mockObject', (object,), {"text": "bad-xml-string"}))
def test_get_bugs_bad_xml_string_in_response(*_args, **_kwargs):
    """
    requirement: if MongoDB Jira API request returns a non-xml document,
    ValueError("Vendor integration error - MongoDB data APIs are not working properly") should be raised
    mock: MongoApiClient
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    try:
        MongoApiClient.get_bugs(self=MockMongoApiClient(), jql_statement="test-query")
        assert False
    except ValueError:
        assert True
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda **kwargs: type(
        'mockObject', (object,),
        {"text": b'<?xml version="1.0" encoding="UTF-8"?><test></test>'}
    )
)
def test_get_bugs_wrong_xml_schema_in_response(*_args, **_kwargs):
    """
    requirement: if MongoDB Jira API request returns an XML document with an unexpected schema
    IndexError("Vendor integration error - MongoDB data APIs are not working properly") should be raised
    mock: MongoApiClient
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    try:
        MongoApiClient.get_bugs(self=MockMongoApiClient(), jql_statement="test-query")
        assert False
    except IndexError:
        assert True
    del sys.modules['vendor_mongodb_api_client']


########################################################################################################################
#                                           managed_products_sn_sync                                                   #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@patch('download_manager.download_instance', lambda **kwargs: False)
def test_managed_products_sn_sync_sn_connection_error(*_args, **_kwargs):
    """
    requirement: request to service now should return a response and when false a
    ConnectionError(f"SN API connection error") should be raised
    mock: MongoApiClient, managed_product, sn_api_url, sn_auth_token
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    try:
        managed_product = type("mockManagedProduct", (object,), {"name": "testProduct", "vendorData": {}})
        MongoApiClient.managed_products_sn_sync(
            self=MockMongoApiClient(),
            managed_product=managed_product,
            sn_api_url="mock_url",
            sn_auth_token="mock_auth_token"
        )
        assert False
    except ConnectionError:
        assert True
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *args, **kwargs: type(
        "mockResponse", (object,), {"text": "non-json-string", "headers": {"x-total-count": 1}}
    )
)
def test_managed_products_sn_sync_json_decode_error(*_args, **_kwargs):
    """
    requirement: request to service now should return a json string and when not a
    ValueError(f"serviceNow API error - response parse error") should be raised
    mock: MongoApiClient, managed_product, sn_api_url, sn_auth_token, response
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    try:
        managed_product = type("mockManagedProduct", (object,), {"name": "testProduct", "vendorData": {}})
        MongoApiClient.managed_products_sn_sync(
            self=MockMongoApiClient(),
            managed_product=managed_product,
            sn_api_url="mock_url",
            sn_auth_token="mock_auth_token"
        )
        assert False
    except ValueError:
        assert True
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@patch(
    'download_manager.download_instance',
    lambda *args, **kwargs: type(
        "mockResponse", (object,), {"text": '{"result": []}', "headers": {"x-total-count": 1}}
    )
)
def test_managed_products_sn_sync_0_running_instances(*_args, **_kwargs):
    """
    requirement: request to service now json response should have at least 1 running instance
    mock: MongoApiClient, managed_product, sn_api_url, sn_auth_token, response
    description: the response json "result" is an empty list and thus a
    ValueError("serviceNow API error - failed to find active mongoDB instance") should be raised
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    try:
        managed_product = type("mockManagedProduct", (object,), {"name": "testProduct", "vendorData": {}})
        MongoApiClient.managed_products_sn_sync(
            self=MockMongoApiClient(),
            managed_product=managed_product,
            sn_api_url="mock_url",
            sn_auth_token="mock_auth_token"
        )
        assert False
    except ValueError:
        assert True
    del sys.modules['vendor_mongodb_api_client']


@patch.dict(os.environ, mock_env())
@patch('sqlalchemy.orm.attributes')
@patch(
    'download_manager.download_instance',
    lambda *args, **kwargs: type(
        "mockResponse", (object,),
        {"text": '{"result": [{"version": "4.4.4"}, {"version": "4.4.2"}]}', "headers": {"x-total-count": 1}}
    )
)
def test_managed_products_sn_sync_2_instances(*_args, **_kwargs):
    """
    requirement: managed_products_sn_sync should populate the instance sn_versions with all the unique versions found
    in the available mongo_db instances discoverd by sn
    mock: MongoApiClient, sqlalchemy.orm.attributes, managed_product, sn_api_url, sn_auth_token, response
    description: 2 instances with unique versions are mocked and thus len(sn_versions) == 2
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    managed_product = type(
        "mockManagedProduct", (object,), {"name": "testProduct", "vendorData": {"productSoftwareVersions": 0}}
    )
    instance = MockMongoApiClient()
    MongoApiClient.managed_products_sn_sync(
        self=instance,
        managed_product=managed_product,
        sn_api_url="mock_url",
        sn_auth_token="mock_auth_token"
    )
    assert len(instance.sn_versions) == 2
    del sys.modules['vendor_mongodb_api_client']


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
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    assert MongoApiClient.timestamp_format(time_str=time_str) == expected_value


########################################################################################################################
#                                                create_managed_product                                                #
########################################################################################################################
@patch.dict(os.environ, mock_env())
def test_create_managed_product_operational_error(*_args, **_kwargs):
    """
    requirement: create a basic MongoDB Server managedProduct if no managed products are found following a db query
    mock: db_client, vendor_config, operational_error
    description: the query fails with an operational error that should be returned
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    instance = MockMongoApiClient()
    vendor_config = type(
        "mockObject", (object,),
        {"value":
            {"vendorPriorities": "test", "vendorStatuses": "test", "vendorResolutionStatuses": "test",
                "vendorProjects": "test"}
         }
    )
    try:
        MongoApiClient.create_managed_product(
            self=instance, db_client=MockDbClient, managed_products_table="testManagedProducts",
            vendor_config=vendor_config
        )
        assert False
    except OperationalError:
        assert True


########################################################################################################################
#                                                create_managed_product                                                #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "html_string, stripped_html_string",
    [
        (
                '<i><span>asdasdsad</span></i>',
                '<i>asdasdsad</i>'
        ),
        (
                '<div><span style="test: test"><div>test text</div></span></div>',
                '<div><div>test text</div></div>'),
        (
                '<body><div><span></span><div><span class="test-span"></span></div></div></body>',
                '<body><div><div></div></div></body>'),
        (
                "<span></span>", ""
        ),
    ]
)
def test_strip_html_spans(html_string, stripped_html_string):
    """
    requirement: create a basic MongoDB Server managedProduct if no managed products are found following a db query
    mock: db_client, vendor_config, operational_error
    description: the query fails with an operational error that should be returned
    :param html_string:
    :param stripped_html_string:
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    assert MongoApiClient.strip_html_spans(html_string) == stripped_html_string


########################################################################################################################
#                                                  create_jql_query                                                    #
########################################################################################################################
@patch.dict(os.environ, mock_env())
@pytest.mark.parametrize(
    "search_filter_map, query",
    [
        (filter_map_example_1, jql_query_1),
        (filter_map_example_2, jql_query_2),
        (filter_map_example_3, jql_query_3)
    ]
)
def test_create_jql_query(search_filter_map, query):
    """
    requirement: given a search_filter_map create the right JQL query
    mock: search_filter_map
    description: test 3 random filter_maps and their expected JQL query value
    :param search_filter_map:
    :param query:
    :return:
    """
    # test a db operational error
    from vendor_mongodb_api_client import MongoApiClient
    assert MongoApiClient.create_jql_query(search_filter_map) == query

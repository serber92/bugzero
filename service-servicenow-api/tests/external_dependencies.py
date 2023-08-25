"""
a collection of mock variables and methods
"""
import logging
import os

import requests
from sqlalchemy.exc import OperationalError

root_folder = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger()
mock_bug_table_class = type("bugs", (object, ), {
    **{x: type("mock", (object,),
               {"prop": type("mock", (object,),
                             {"columns": [
                                 type("managedProduct", (object,), {"type": 1}),
                                 type("bugs", (object,), {"type": 1}),
                             ]
                             },
                             ),
                }) for x in ["vendorData", "snCiFilter", "snCiTable", "bugId", "managedProductId",
                             "vendorLastUpdatedDate"]
       },
    **{
        "__init__": lambda *_args, **_kwargs: None,
    }
})
mock_managed_products_2 = [
    type("managedProduct", (object,), {"lastExecution": 1, "name": "testProduct1", "isDisabled": 0}),
    type("managedProduct", (object,), {"lastExecution": 1, "name": "testProduct2", "isDisabled": 0}),
]
mock_varchar_table = type("test", (object, ), {
    **{x: type("mock", (object,),
               {"prop": type("mock", (object,),
                             {"columns": [
                                 type("bugs", (object,), {
                                     "type":  type("type", (object,), {
                                         "type": "test", "length": 8
                                     }),
                                 }),
                             ]
                             },
                             ),
                }) for x in ["vendorData", "snCiFilter", "snCiTable", "bugId", "managedProductId",
                             "vendorLastUpdatedDate"]
       },
    **{
        "__init__": lambda *_args, **_kwargs: None,
    }
})
mock_session = type("session", (object,), {
    "post": lambda **_kwargs: type("sessionPost", (object,), {"status_code": 200}),
    "get": lambda **_kwargs: type("sessionPost", (object,), {"status_code": 200}),
})
mock_session_w_post_404 = type("session", (object,), {
    "post": lambda **_kwargs:
    type("sessionPost", (object,), {"status_code": 404, "url": "http://failed-url.com", "text": ""})
})

class MockLastExecution(int):
    """
    last execution variable for DB class
    """
    def is_(self, *_args):
        """

        :param _args:
        :return:
        """
        if self:
            return None
        else:
            return None


class SessionMock:
    """
    requests session mock that raises a connection error on post
    """
    @staticmethod
    def post(url, timeout, headers, data):
        """

        :param url:
        :param timeout:
        :param headers:
        :param data:
        :return:
        """
        raise requests.exceptions.ConnectionError

def mock_env():
    """
    mock environment variables
    :return:
    """
    return {
        "SETTINGS_TABLE": "", "MANAGED_PRODUCTS_TABLE": "managedProducts", "SERVICES_TABLE": "", "VENDORS_TABLE": "",
        "SERVICE_EXECUTION_TABLE": "", "DB_HOST": "", "DB_PORT": "", "DB_NAME": "", "DB_USER": "", "DB_PASS": "",
        "BUGS_TABLE": "", "AWS_DEFAULT_REGION": "us-east-1", "BZ_SN_PORTAL_BASIC_AUTH_KEY": "",
        "BZ_SN_PORTAL_URL": "https://www.test.com"
    }


def mock_operational_error(*_args, **_kwargs):
    """
    force an sqlalchemy OperationalError
    :param _args:
    :param _kwargs:
    :return:
    """
    raise OperationalError("test", "test", "test")


def mock_requests_read_timeout(*_args, **_kwargs):
    """
    force a requests.exceptions.ReadTimeout
    :param _args:
    :param _kwargs:
    :return:
    """
    raise requests.exceptions.ReadTimeout("ReadTimeout")


def mock_requests_connection_timeout(*_args, **_kwargs):
    """
    force a requests.exceptions.ConnectTimeout
    :param _args:
    :param _kwargs:
    :return:
    """
    raise requests.exceptions.ConnectTimeout("ConnectTimeout")


def mock_requests_connection_error(*_args, **_kwargs):
    """
    force a requests.exceptions.ConnectionError
    :param _args:
    :param _kwargs:
    :return:
    """
    raise requests.exceptions.ConnectionError("ConnectionError")


def mock_connection_error(*_args, **_kwargs):
    """
    simulate a connectionError exception
    :param _args:
    :param _kwargs:
    :return:
    """
    raise ConnectionError("Vendor integration error - MongoDB data APIs are not working properly")


def mock_managed_products_query_result_no_version(*_args, **_kwargs):
    """
    mocked list of 1 managedProduct with an empty productSoftwareVersions field
    :param _args:
    :param _kwargs:
    :return:
    """
    return [
        type("mockManagedProduct", (object,), {
            "vendorData": {"productSoftwareVersions": []},
            "add": lambda *_args: True,
            "name": "Test",
            "id": "test"
        })

    ]


def mock_managed_products_query_result(*_args, **_kwargs):
    """
    mocked list of 1 managedProduct with an empty productSoftwareVersions field
    :param _args:
    :param _kwargs:
    :return:
    """
    return [
        type("mockManagedProduct", (object,), {
            "vendorData": {"productSoftwareVersions": ["5.5.5"]},
            "add": lambda *_args: True,
            "name": "Test",
            "lastExecution": None,
            "id": "test"
        })

    ]


class MockDbClient:
    """

    """
    def __init__(self, *_args, **_kwargs):
        """

        :param args:
        :param kwargs:
        """
        pass
    conn = type(
        "conn", (object,),
        {
            "commit": lambda **_kwargs: type("mockObject", (object,), {}),
            "refresh": lambda *_args, **_kwargs: mock_operational_error(),
            "add": lambda *_args: True,
            "query": lambda *_args, **_kwargs:
            type("query", (object,),
                 {"filter_by": lambda *_args, **_kwargs: type("mockObject", (object,), {
                     "first": lambda *_args: type("mockObject", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                  "get": lambda x: type("mockObject", (object,), {"value": True}),
                  "filter": lambda *_args, **_kwargs: type(
                      "mockObject", (object,), {
                          "or_": lambda *_args: type(
                              "mockObject", (object,), {"active": True}),
                          "all": lambda *_args: [],
                          "first": lambda *_args: False,
                      }
                  ),
                  },
                 )
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "test": lambda **_kwargs: True,
                "testManagedProducts": type("mockClass", (object,),
                                            {"vendorId": True, "__init__": lambda *_args, **_kwargs: None}),
                "":  type("class", (object,), {"active": True}),

            }
        }
    )

    @staticmethod
    def create_session():
        """

        :return:
        """
        return True


class MockEmptyDbClient:
    """
    a db client instance that has zero bugs
    """
    def __init__(self, *_args, **_kwargs):
        """

        :param args:
        :param kwargs:
        """
        pass
    conn = type("conn", (object,), {
        "commit": lambda **_kwargs: type("query", (object,), {}),
        "add": lambda *_args: True,
        "query": lambda *_args, **_kwargs:
        type("query", (object,), {"filter_by": lambda *_args, **_kwargs: type("query", (object,), {
            "first": lambda *_args: type("query", (object,), {"active": True}),
            "all": lambda *_args: [], },),
                                  "get": lambda *_args, **_kwargs: False,
                                  }
             )
    })
    base = type("base", (object,), {
        "classes": {
            "test": lambda **_kwargs: True,
            "":  type("class", (object,), {"active": True}),

        }
    })

    @staticmethod
    def create_session():
        return True


class MockDbClientWithManagedProductsNoBugs:
    def __init__(self, *_args, **_kwargs):
        """
        db instance with managedProducts and 0 bugs
        :param args:
        :param kwargs:
        """
        pass
    conn = type(
        "conn", (object,),
        {
            "commit": lambda **_kwargs: type("query", (object,), {}),
            "add": lambda *_args: True,
            "query": lambda *_args, **_kwargs:
            type("query", (object,),
                 {
                     "filter": lambda *_args, **_kwargs: type(
                         "filter", (object,), {
                             "or_": lambda *_args: type(
                                 "or", (object,), {"active": True}),
                             "all": lambda *_args: mock_managed_products_2,
                             "first": lambda *_args: False,
                         }
                     ),
                     "filter_by":
                         lambda *_args, **_kwargs:
                         type("filter_by", (object,), {
                             "first": lambda *_args: type(
                                 "first", (object,), {"active": True}),
                             "all": lambda *_args: [], },
                              ),
                     "get": lambda x: type("query", (object,), {"value": {"snAuthToken": "", "snApiUrl": ""}}),
                 }
                 )
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "bugs_table": mock_bug_table_class,
                "test": lambda **_kwargs: True,
                "managedProducts":  type(
                    "mockClass", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "mongodb"
                    }
                ),
                "": type(
                        "mockClass", (object,),
                        {
                            "name": "test",
                            "lastExecution": MockLastExecution(),
                            "isDisabled": 1,
                            "vendorId": "mongodb",
                            "id": "1",
                            "active": True,
                        }
                )


            }
        }
    )

    @staticmethod
    def create_session():
        return True

"""
a collection of mock variables and methods
"""
import datetime
import logging

import requests
from botocore.exceptions import ClientError
from sqlalchemy.exc import OperationalError

logger = logging.getLogger()

mock_bad_credentials_verification_event = {
    "serviceApiClientId": "",
    "serviceApiClientSecret": "",
    "supportApiClientId": "",
    "supportApiClientSecret": "",

}

mock_good_credentials_verification_event = {
    "serviceApiClientId": True,
    "serviceApiClientSecret": True,
    "supportApiClientId": True,
    "supportApiClientSecret": True,
}
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


class MockDbClientManagedProductsEmpty:
    def __init__(self, *_args, **_kwargs):
        """
        db instance with 0 managedProducts
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
            type("query", (object,), {
                "filter": lambda *_args, **_kwargs: type(
                    "filter", (object,), {
                        "or_": lambda *_args: type(
                            "or", (object,), {"active": True}),
                        "all": lambda *_args: [],
                        "first": lambda *_args: [],
                    }
                ),
                "filter_by": lambda *_args, **_kwargs:
                type(
                    "filter_by", (object,), {
                        "first": lambda *_args: type(
                            "first", (object,), {"active": True}),
                        # mock a manageProduct
                        "all": lambda *_args: mock_managed_products_2},
                ),
                "get": lambda x: type("query", (object,), {"value": {"serviceSecretId": True}}),
            }
                 )
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "test": lambda **_kwargs: True,
                "managedProducts":  type(
                    "class", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "vmware",

                    }
                ),
                "services":  type(
                    "class", (object,),
                    {
                        "id": "services_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),
                "vendors":  type(
                    "class", (object,),
                    {
                        "id": "vendors_table",
                        "__init__": lambda *_args, **_kwargs: None,
                        "active": True
                    }
                ),
                "settings":  type(
                    "class", (object,),
                    {
                        "id": "settings_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),
                "serviceExecution":  type(
                    "class", (object,),
                    # managed products
                    {
                        "id": "service_execution_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),



            }
        }
    )

    @staticmethod
    def create_session():
        """

        :return:
        """
        return True


class MockDbClientExistingServiceEntry:
    def __init__(self, *_args, **_kwargs):
        """
        db instance with 0 managedProducts
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
            type("mockObject", (object,), {
                "filter": lambda *_args, **_kwargs: type(
                    "mockObject", (object,), {
                        "or_": lambda *_args: type(
                            "mockObject", (object,), {"active": True}),
                        "all": lambda *_args: [],
                        "first": lambda *_args: type("query", (object,),
                                                     {"status": "", "lastExecution": "", "message": ""}),
                    }
                ),
                "filter_by": lambda *_args, **_kwargs:
                type(
                    "mockObject", (object,), {
                        "first": lambda *_args: type(
                            "mockObject", (object,), {"active": True}),
                        # mock a manageProduct
                        "all": lambda *_args: mock_managed_products_2},
                ),
                "get": lambda x: type("query", (object,), {"value": {"serviceSecretId": True}}),
            }
                 )
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "test": lambda **_kwargs: True,
                "managedProducts":  type(
                    "class", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "vmware",

                    }
                ),
                "services":  type(
                    "class", (object,),
                    {
                        "id": "services_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),
                "vendors":  type(
                    "class", (object,),
                    {
                        "id": "vendors_table",
                        "__init__": lambda *_args, **_kwargs: None,
                        "active": True
                    }
                ),
                "settings":  type(
                    "class", (object,),
                    {
                        "id": "settings_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),
                "serviceExecution":  type(
                    "class", (object,),
                    # managed products
                    {
                        "id": "service_execution_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),



            }
        }
    )

    @staticmethod
    def create_session():
        """

        :return:
        """
        return True


class MockSecrectManagerClient:
    """
    AWS secret client mock
    """
    def __init__(self, **_kwargs):
        """

        :param _kwargs:
        """
        if "secret_string" in _kwargs:
            self.secret_string = _kwargs['secret_string']
        else:
            self.secret_string = ""
        if 'secret_binary' in _kwargs:
            self.secret_binary = _kwargs['secret_binary']
        else:
            self.secret_binary = ""
        self.secret_manager_client = self
        if 'binary_error' in _kwargs:
            raise ClientError(error_response={}, operation_name="test")

        self.logger = logging.getLogger()

    def get_secret_value(self, **_kwargs):
        """

        :param _kwargs:
        :return:
        """
        if self.secret_string:
            return {"SecretString": self.secret_string}
        if self.secret_binary:
            return {"SecretBinary": ""}


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


class MockMongoApiClient:
    """

    :return:
    """
    def __init__(
            self,
            service_now_ci_table="cmdb_ci_db_mongodb_instance",
            vendor_id="MongoDb"
    ):
        """
        """
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = dict()
        self.logger = logger
        self.service_now_ci_table = service_now_ci_table
        self.sn_query_cache = {}
        self.sn_versions = []
        self.vendor_id = vendor_id
        self.thread_error_tracker = 0
        self.issues_endpoint_url = \
            "https://jira.mongodb.org/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?" \
            "jqlQuery={}&" \
            "tempMax=100000"

    @staticmethod
    def strip_html_spans(_html_string):
        return _html_string

    @staticmethod
    def timestamp_format(_time_str):
        return datetime.datetime.now()


def mock_env():
    """
    mock environment variables
    :return:
    """
    return {
        "SETTINGS_TABLE": "settings", "MANAGED_PRODUCTS_TABLE": "managedProducts", "SERVICES_TABLE": "services",
        "VENDORS_TABLE": "vendors", "SERVICE_EXECUTION_TABLE": "serviceExecution", "DB_HOST": "", "DB_PORT": "",
        "DB_NAME": "", "DB_USER": "", "DB_PASS": "", "BUGS_TABLE": "bugs", "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "", "AWS_SECRET_ACCESS_KEY": ""
    }


def mock_response_instance(response_text, return_false=False):
    """

    :param response_text:
    :param return_false:
    :return:
    """
    if return_false:
        return lambda *_args, **_kwargs: False
    return lambda *_args, **_kwargs: type("responseInstanceMock", (object,),
                                          {"text": response_text, "url": 'client_id=1&'})


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
    raise ConnectionError("ConnectionError")


def mock_connect_name_error(*_args, **_kwargs):
    """
    simulate a NameError exception resulting from bad credentials
    :param _args:
    :param _kwargs:
    :return:
    """
    raise NameError("NameError")


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
                "settingsTable":  type("class", (object,), {"active": True}),

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
        type("query", (object,),
             {
                 "filter_by": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: type("query", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                 "get": lambda *_args, **_kwargs: False,
                 "filter": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: type("query", (object,), {"active": True}),
                     "all": lambda *_args: [], },),

                                  }
             )
    })
    base = type("base", (object,), {
        "classes": {
            "test": lambda **_kwargs: True,
            "settings":  type("mockClass", (object,), {"active": True}),
            "vendors":  type("mockClass", (object,), {"active": True}),
            "bugs":  type("mockClass", (object,),
                          {
                              "bugId": type("mockObject", (object,),
                                         {"prop": type("mockObject", (object,),
                                                       {"columns": [type("mockObject", (object,),
                                                                        {"type": "NON-VARCHAR"})]})
                                          }
                                         ),
                              "managedProductId": type("mockObject", (object,),
                                         {"prop": type("mockObject", (object,),
                                                       {"columns": [type("mockObject", (object,),
                                                                         {"type": "NON-VARCHAR"})]})
                                          }
                                         )
                           }
                          )

        }

    })

    @staticmethod
    def create_session():
        return True


class MockDbClientOperationalError:
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
        type("query", (object,),
             {
                 "filter_by": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: type("query", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                 "get": lambda *_args, **_kwargs: type("query", (object,), {"value": True}),
                 "filter": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: True,
                     "all": lambda *_args: [], },),

             }
             )
    })
    base = type("base", (object,), {
        "classes": {
            "test": lambda **_kwargs: True,
            "settings":  type("mockClass", (object,), {"active": True}),
            "vendors":  type("mockClass", (object,), {"active": True}),
            "managedProducts":  type("mockClass", (object,), {"name": "testProduct",
                                                              "lastExecution": datetime.datetime.now(),
                                                              "isDisabled": 0,
                                                              "vendorId": "cisco"
                                                              }),
            "bugs":  type("mockClass", (object,),
                          {
                              "__init__": lambda *_args, **_kwargs: mock_operational_error(),
                              "bugId": type("mockObject", (object,),
                                            {"prop": type("mockObject", (object,),
                                                          {"columns": [type("mockObject", (object,),
                                                                            {"type": "NON-VARCHAR"})]})
                                             }
                                            ),
                              "managedProductId": type("mockObject", (object,),
                                                       {"prop": type("mockObject", (object,),
                                                                     {"columns": [type("mockObject", (object,),
                                                                                       {"type": "NON-VARCHAR"})]})
                                                        }
                                                       )
                          }
                          )

        }

    })

    @staticmethod
    def create_session():
        return True


class MockDbClientSkipManagedProducts:
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
        type("query", (object,),
             {
                 "filter_by": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: type("query", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                 "get": lambda *_args, **_kwargs: type("query", (object,), {"value": True}),
                 "filter": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: True,
                     "all": lambda *_args: [type("query", (object,),
                                                 {"name": "testProduct1",
                                                  "isDisabled": 0,
                                                  "lastExecution": datetime.datetime.now()}
                                                 ),
                                            ], },),

             }
             )
    })
    base = type("base", (object,), {
        "classes": {
            "test": lambda **_kwargs: True,
            "settings":  type("mockClass", (object,), {"active": True}),
            "vendors":  type("mockClass", (object,), {"active": True}),
            "managedProducts":  type("mockClass", (object,), {"name": "testProduct",
                                                              "lastExecution": datetime.datetime.now(),
                                                              "isDisabled": 0,
                                                              "vendorId": "cisco"
                                                              }),
            "bugs":  type("mockClass", (object,),
                          {
                              "__init__": lambda *_args, **_kwargs: mock_operational_error(),
                              "bugId": type("mockObject", (object,),
                                            {"prop": type("mockObject", (object,),
                                                          {"columns": [type("mockObject", (object,),
                                                                            {"type": "NON-VARCHAR"})]})
                                             }
                                            ),
                              "managedProductId": type("mockObject", (object,),
                                                       {"prop": type("mockObject", (object,),
                                                                     {"columns": [type("mockObject", (object,),
                                                                                       {"type": "NON-VARCHAR"})]})
                                                        }
                                                       )
                          }
                          )

        }

    })

    @staticmethod
    def create_session():
        return True


class MockDbClientNoExistingBugs:
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
        type("query", (object,),
             {
                 "filter_by": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: type("query", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                 "get": lambda *_args, **_kwargs: False,
                 "filter": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: False,
                     "all": lambda *_args: [], },),

             }
             )
    })
    base = type("base", (object,), {
        "classes": {
            "test": lambda **_kwargs: True,
            "settings":  type("mockClass", (object,), {"active": True}),
            "vendors":  type("mockClass", (object,), {"active": True}),
            "bugs":  type("mockClass", (object,),
                          {
                              "__init__": lambda *_args, **_kwargs: mock_operational_error(),
                              "bugId": type("mockObject", (object,),
                                            {"prop": type("mockObject", (object,),
                                                          {"columns": [type("mockObject", (object,),
                                                                            {"type": "NON-VARCHAR"})]})
                                             }
                                            ),
                              "managedProductId": type("mockObject", (object,),
                                                       {"prop": type("mockObject", (object,),
                                                                     {"columns": [type("mockObject", (object,),
                                                                                       {"type": "NON-VARCHAR"})]})
                                                        }
                                                       )
                          }
                          )

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
                "bugs": mock_bug_table_class,
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
                "settings":  type("class", (object,), {"active": True}),
                "vendors":  type("class", (object,), {"active": True}),
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

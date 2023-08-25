"""
a large collection of mock variables and methods
"""
import datetime
import json
import logging

import requests
from botocore.exceptions import ClientError
from sqlalchemy.exc import OperationalError
from tests.mock_json_payload import mock_kb_data

mock_existing_bug_old = type("managedProduct", (object,), {"vendorLastUpdatedDate": -1})
mock_existing_similar_old = type("managedProduct", (object,), {"vendorLastUpdatedDate": 22})
mock_managed_products_2 = [
    type("managedProduct", (object,), {"lastExecution": 1, "name": "testProduct1", "isDisabled": 0}),
    type("managedProduct", (object,), {"lastExecution": 1, "name": "testProduct2", "isDisabled": 0}),
]
mock_collector_status_response_not_healthy = json.dumps([
    {"name": "collector1", "state": "ERROR"}
])
mock_collector_status_response_healthy = json.dumps([
    {"name": "collector1", "state": "HEALTHY"}
])
mock_skyline_rule_list = json.dumps({
        "ruleList": [
            {
                "ruleDisplayName": "KB#111111111", "state": "HEALTHY", "ruleId": "test", "ruleDescription": "",
                "severity": "", "recommendations": "", "findingTypes": "", "ruleImpact": "", "totalObjectsCount": "",
                "categoryName": ""

            },
            {
                "ruleDisplayName": "-cve-", "state": "HEALTHY", "ruleId": "test", "ruleDescription": "",
                "severity": "", "recommendations": "", "findingTypes": "", "ruleImpact": "", "totalObjectsCount": "",
                "categoryName": ""

            }
        ],
        "totalCount": 1
    })
mock_bad_credentials_verification_event = {
    "password": "",
    "username": "",
    "orgId": "",
}
mock_bad_orgId_credentials_verification_event = {
    "password": "",
    "username": "",
    "orgId": False,
}
mock_bad_good_credentials_verification_event = {
    "password": True,
    "username": True,
    "orgId": True,
}
mock_session = type("session", (object,), {
    "post": lambda **_kwargs: type("sessionPost", (object,), {"status_code": 200}),
    "get": lambda **_kwargs: type("sessionPost", (object,), {"status_code": 200}),
})
mock_session_w_post_404 = type("session", (object,), {
    "post": lambda **_kwargs:
    type("sessionPost", (object,), {"status_code": 404, "url": "http://failed-url.com", "text": ""})
})
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
mock_product_by_morid_no_bugs = {
    "ESXi": {"snCiTable": "cmdb_ci_esx_server", "hosts": set(),
             "managedProduct": type("managedProduct", (object,), {"lastExecution": ""}),
             "bugs": {}},
    "vCenter": {"snCiTable": "cmdb_ci_vcenter", "hosts": set(),
                "managedProduct": type("managedProduct", (object,), {"lastExecution": ""}),
                "bugs": {},
                "versions": set()}
}

mock_product_by_morid_1_bug = {
    "ESXi": {"snCiTable": "cmdb_ci_esx_server", "hosts": set(), "managedProduct": mock_managed_products_2[0],
             "bugs": {
                 "bug1": {
                     "vendorData": {'morIds': {"1", "2", "3"}, 'vc_versions': {"1", "2", "3"}},
                     "bugId": "bug1", "managedProductId": "1", "vendorLastUpdatedDate": 22
                 }
             }
             },
    "vCenter": {"snCiTable": "cmdb_ci_vcenter", "hosts": set(), "managedProduct": mock_managed_products_2[1],
                "bugs": {},
                "versions": set()}
}


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


class MockVmwareApiInstance:
    """

    :param _args:
    :param _kwargs:
    :return:
    """
    def __init__(self, **_kwargs):
        """

        :param _kwargs:
        """
        self.earliest_execution = datetime.datetime.now()
        self.logger = logging.getLogger(__name__)
        self.vendor_id = "vmware"
        self.bug_ids = set()
        self.dedup_count = 0
        self.secret_manager_client = False
        self.cached_kb_data = {}
        self.bug_search_filters = lambda **_kwargs: False
        if "overwrite_kb_data" not in _kwargs:
            self.get_kb_data = lambda **_kwargs: mock_kb_data()
        self.cached_kb_data = _kwargs["cached_kb_data"] if 'cached_kb_data' in _kwargs else []


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

    def get_secret_value(self, **_kwargs):
        """

        :param _kwargs:
        :return:
        """
        if self.secret_string:
            return {"SecretString": '{"1st_field": ""}'}
        if self.secret_binary:
            return {"SecretBinary": ""}


def mock_db_client(*_args, **_kwargs):
    """

    :return:
    """
    return MockDbClient


def mock_get_auth():
    """

    :return:
    """
    return lambda *_args: True, True


def mock_vmware_config(config_example):
    """

    :return:
    """
    return config_example


def mock_os_environ():
    """

    :return:
    """
    return {
        "environ":
            {
                "DB_HOST": "test_db",
                "DB_PORT": "test_db",
                "DB_USER": "test_db",
                "DB_PASS": "test_db",
                "DB_NAME": "test_db",
                "VENDORS_TABLE": "test_db",
                "SERVICE_EXECUTION_TABLE": "test_db",
                "SERVICES_TABLE": "test_db",
                "SETTINGS_TABLE": "test_db",
                "MANAGED_PRODUCTS_TABLE": "test_db",
            }
    }


def mock_skyline_inventory():
    """
    returm mock payload for skyline inventory
    :return:
    """
    return {
        "inventory": [
            {
                "type": "vc",
                "version": "test_3",
                "datacenters": [
                    {
                        "clusters": [
                            {
                                "hosts": [
                                    {"version": "test_1"},
                                    {"version": "test_2"}
                                ]
                            },
                            {
                                "hosts": [
                                    {"version": "test_1"},
                                    {"version": "test_2"}
                                ]
                            }
                        ]
                    },

                ]
            },

        ]
    }


def mock_managed_products():
    """
    return a list of relevant managedProducts
    :return:
    """
    return [
        type(
            'managedProducts',
            (object,),
            {
                'name': "ESXi",
                'vendorData': {"productSoftwareVersions": ["test_1", "test_2"]}
            }
        ),
        type(
            'managedProducts',
            (object,),
            {
                'name': "vCenter",
                'vendorData': {"productSoftwareVersions": ["test_3", "test_4"]}
            }
        )
    ]


def mock_other_managed_products():
    """
    return a list of not relevant managedProducts
    :return:
    """
    return [type('managedProducts', (object,), {'name': "test"}), ]


def mock_env():
    """
    mock environment variables
    :return:
    """
    return {
        "SETTINGS_TABLE": "", "MANAGED_PRODUCTS_TABLE": "", "SERVICES_TABLE": "", "VENDORS_TABLE": "",
        "SERVICE_EXECUTION_TABLE": "", "DB_HOST": "", "DB_PORT": "", "DB_NAME": "", "DB_USER": "", "DB_PASS": "",
        "BUGS_TABLE": "", "AWS_DEFAULT_REGION": "us-east-1"
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
    create an sqlalchemy OperationalError
    :param _args:
    :param _kwargs:
    :return:
    """
    raise OperationalError("test", "test", "test")


def mock_value_error(*_args, **_kwargs):
    """
    value error mock
    :param _args:
    :param _kwargs:
    :return:
    """
    raise ValueError("test", "test", "test")


def mock_vmware_api_client(mock_client):
    """

    :param mock_client:
    :return:
    """
    return mock_client


class VmWareConfig:
    """

    """
    value = ""


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
            "commit": lambda **_kwargs: type("query", (object,), {}),
            "add": lambda *_args: True,
            "query": lambda *_args, **_kwargs:
            type("query", (object,),
                 {"filter_by": lambda *_args, **_kwargs: type("query", (object,), {
                     "first": lambda *_args: type("query", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                  "get": lambda x: type("query", (object,), {"value": True}),
                  })
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "test": lambda **_kwargs: True,
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
                        "all": lambda *_args: [], },
                ),
                "get": lambda x: type("query", (object,), {"value": True}),
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
                "services_table":  type(
                    "class", (object,),
                    # managed products
                    {
                        "id": "services_table",
                        "__init__": lambda *_args, **_kwargs: None
                    }
                ),
                "service_execution_table":  type(
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
                     "get": lambda x: type("query", (object,), {"value": True}),
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
                    "class", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "vmware"
                    }
                ),


            }
        }
    )


class MockDbClientWithManagedProductsWithExistingOldBug:
    def __init__(self, *_args, **_kwargs):
        """
        db instance with managedProducts with 1 bug that needs to be updated
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
                             # makes the existingBug return True
                             "first": mock_existing_bug_old,
                         }
                     ),
                     "filter_by": lambda *_args, **_kwargs: type(
                         "filter_by", (object,), {
                             "first": lambda *_args: type(
                                 "first", (object,), {"active": True}),
                             "all": lambda *_args: [], },
                     ),
                     "get": lambda x: type("query", (object,), {"value": True}),
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
                    "class", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "vmware"
                    }
                ),


            }
        }
    )


class MockDbClientWithManagedProductsWithExistingSimilarBug:
    """
    db instance with managedProducts with 1 bug that is up to date
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
                             # makes the existingBug return True
                             "first": mock_existing_similar_old,
                         }
                     ),
                     "filter_by": lambda *_args, **_kwargs:
                     type(
                         "filter_by", (object,), {
                             "first": lambda *_args: type(
                                 "first", (object,), {"active": True}),
                             "all": lambda *_args: [], },
                     ),
                     "get": lambda x: type("query", (object,), {"value": True}),
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
                    "class", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "vmware"
                    }
                ),


            }
        }
    )

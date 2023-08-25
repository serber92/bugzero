"""
a collection of mock variables and methods
"""
import datetime
import json
import logging
import os

import requests
from botocore.exceptions import ClientError
from sqlalchemy.exc import OperationalError

from vendor_exceptions import VendorConnectionError

root_folder = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger()

mock_netapp_managed_product = type("mockManagedProduct", (object,), {"name": "testProduct", "id": "1"})

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
    type("managedProduct", (object,), {"lastExecution": 1, "name": "testProduct1", "isDisabled": 0,
                                       "vendorPriorities": [{"vendorPriority": "1"}], "vendorStatuses": ["1"],
                                       "vendorData": {"vendorProductModelId": "model1"}}),
    type("managedProduct", (object,), {"lastExecution": 1, "name": "testProduct2", "isDisabled": 0,
                                       "vendorPriorities": [{"vendorPriority": "2"}], "vendorStatuses": ["2"],
                                       "vendorData": {"vendorProductModelId": "model2"}}),
]

mock_managed_product = type(
    "managedProduct", (object,),
    {"versions": [], "updatedAt": "", "isDisabled": 0, "name": "testProduct1", "vendorData": {}})

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

netapp_bugs_w_versions_examples = json.loads(
    open(f'{root_folder}/netapp_bugs_without_affected_versions.json', 'r').read()
)

netapp_bugs_missing_mandatory_field_examples = json.loads(
    open(f'{root_folder}/netapp_bugs_missing_mandatory_fields.json', 'r').read()
)

netapp_valid_and_invalid_bug_examples = json.loads(
    open(f'{root_folder}/netapp_valid_and_invalid_bugs.json', 'r').read()
)

netapp_non_bug_risks = json.loads(
    open(f'{root_folder}/netapp_non_bug_risks.json', 'r').read()
)
netapp_bug_risks_no_active_instances = json.loads(
    open(f'{root_folder}/netapp_bug_risks_no_active_instances.json', 'r').read()
)

netapp_bug_risks = json.loads(
    open(f'{root_folder}/netapp_bug_risks_w_active_instances.json', 'r').read()
)

mock_formatted_bugs = [
    {
        "bugId": "1273955",
        "summary": "Read operations that encounter certain internal errors might leak memory, causing gradual performance degradation and system outage",
        "description": "If a read operation in ONTAP attempts to retrieve multiple file blocks, the \ndata corresponding to each file block is extracted in turn from a compacted \nblock. If, due to an internal error, the extraction succeeds for one or more \nof the file blocks, but fails for others, then the read operation attempts \nto retry and correct the error. However, under certain conditions, memory \nallocated to store data for the successfully extracted blocks is not \nreleased. Therefore, there might be a gradual depletion of available system \nmemory or in rare cases a system outage. The functionality of the read \nrequest operation is unaffected; an internal memory leak is the only side \neffect.\n\nMitigation Category:\nPotentially Non-disruptive\n\nMitigation Action:\nPotentially Non-disruptive\n\nImpact Area:\nAvailability\n\nPotential Impact:\nThe system may experience performance degradation and possible panic.\n\nWorkaround:\nContact technical support.",
        "vendorLastUpdatedDate": datetime.datetime.now(),
        "vendorCreatedDate": datetime.datetime.now(),
        "knownAffectedReleases": "9.6, 9.6P1, 9.6P2, 9.6P3, 9.6P4, 9.6P5, 9.6P6, 9.6P7, 9.7, 9.7P1, 9.7P2",
        "knownFixedReleases": "9.10.0, 9.10.0P1, 9.10.1RC1, 9.10.1RC1P1, 9.6P10, 9.6P11, 9.6P12, 9.6P13, 9.6P14, 9.6P15, 9.6P16, 9.6P8, 9.6P9, 9.7P10, 9.7P11, 9.7P12, 9.7P13, 9.7P14, 9.7P15, 9.7P16, 9.7P3, 9.7P4, 9.7P5, 9.7P6, 9.7P7, 9.7P8, 9.7P9, 9.8, 9.8P1, 9.8P2, 9.8P3, 9.8P4, 9.8P5, 9.8P6, 9.8P7, 9.8P8, 9.8RC1, 9.9.0, 9.9.1, 9.9.1P1, 9.9.1P2, 9.9.1P3, 9.9.1P4, 9.9.1P5, 9.9.1RC1",
        "bugUrl": "https://mysupport.netapp.com/site/bugs-online/product/ONTAP/BURT/1273955",
        "snCiTable": "cmdb_ci_storage_server",
        "cis_serial_numbers": {
            "632009000009",
            "621940000283",
            "632009000010",
            "621940000282",
            "622008000080",
            "622008000075",
            "622008000079",
            "622008000076"
        },
        "status": "Fixed",
        "priority": "Critical",
        "managedProductId": 355,
        "vendorId": "netapp",
        "vendorData": {
            "netAppRiskId": "5219",
            "netAppRiskSeverity": "high",
            "bugApiUrl": "https://mysupport.netapp.com/api/bol-service/ONTAP/bugs/BURT/1273955",
            "vendorProductName": "NetApp AFF-C190"
        }
    }
]


class MockSecretManagerClient:
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
        self.binary_error = False
        if 'binary_error' in _kwargs:
            self.binary_error = True

        self.logger = logger

    def get_secret_value(self, **_kwargs):
        """

        :param _kwargs:
        :return:
        """
        if self.binary_error:
            raise ClientError(error_response={}, operation_name="test")
        if self.secret_string:
            return {"SecretString": '{"setting-netapp-supportUser": "1"}'}
        if self.secret_binary:
            return {"SecretBinary": ""}
        return {""}


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


class MockNetAppApiClient:
    """

    :return:
    """
    def __init__(
            self,
            vendor_id="netapp"
    ):
        """

        """
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = []
        self.logger = logger
        self.sn_query_cache = {}
        self.sn_versions = []
        self.vendor_id = vendor_id
        self.oam_session = requests.session()
        self.sn_table = "test"
        self.account_systems = {
            "sys1": {"model": "model1"},
            "0538038214": {"model": "model1"},
            "0537126047": {"model": "model1"},
            "0536906207": {"model": "model1"},
        }

    @staticmethod
    def timestamp_format(_time_str):
        return datetime.datetime.now()

    @staticmethod
    def attach_managed_products(*_args, **_kwargs):
        return type("managedProduct", (object,), {"id": "1", "name": "test", "lastExecution": None})


def mock_env():
    """
    mock environment variables
    :return:
    """
    return {
        "SETTINGS_TABLE": "", "MANAGED_PRODUCTS_TABLE": "managedProducts", "SERVICES_TABLE": "", "VENDORS_TABLE": "",
        "SERVICE_EXECUTION_TABLE": "", "DB_HOST": "", "DB_PORT": "3660", "DB_NAME": "", "DB_USER": "", "DB_PASS": "",
        "BUGS_TABLE": "", "AWS_DEFAULT_REGION": "us-east-1", "EVENT_CLASS": "", "NODE": "", "SNS_TOPIC": ""
    }


def mock_database_init(self, db_host, db_user, db_password, db_port, db_name, base=None, conn=None):
    """
    set database connection variables in class instance
    """
    self.host = db_host
    self.username = db_user
    self.password = db_password
    self.port = int(db_port)
    self.dbname = db_name
    self.base = type("MockDBBase", (object,), {"classes": {
        "bugs": type("mockClass", (object,), {"bugId": ""}),
        "services": type("mockClass", (object,), {"id": ""}),
        "serviceExecution": lambda *_args, **_kwargs: ("mockClass", (object,), {"id": ""}),
    }
    }
                     )
    self.conn = type(
        "MockDBBase", (object,),
        {
            "add": lambda *_args, **_kwargs: True,
            "commit": lambda *_args, **_kwargs: True,
            "close": lambda *_args, **_kwargs: True,
            "query": lambda *_args, **_kwargs:
            type("mockObject", (object,),
                 {
                     "filter": lambda *_args, **_kwargs:
                     type("mockObject", (object,),
                          {
                              "first": lambda *_args, **_kwargs: type(
                                  "mockEntry", (object,), {
                                      "status": "", "lastExecution": "", "message": "", "lastSuccess": ""
                                  }
                              )
                          })
                 }
                 )
        },
    )


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
    raise ConnectionError("Vendor integration error - vendor data APIs are not working properly")


def mock_vendor_connection_exception(*_args, **_kwargs):
    """
    simulate a VendorConnectionError error
    :param _args:
    :param _kwargs:
    :return:
    """
    raise VendorConnectionError(url="", event_message="", internal_message="")


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
            "vendorData": {"vendorResolutions": []},
            "name": "Red Hat Enterprise Linux 2.1",
            "lastExecution": None,
            "isDisabled": 0,
            "vendorPriorities": [],
            "vendorStatuses": [],

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

    @staticmethod
    def get_vendor_config(**kwargs):
        if "success" in kwargs:
            return True
        return False


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
                        "vendorId": "netpp"
                    }
                ),
                "": type(
                        "mockClass", (object,),
                        {
                            "name": "test",
                            "lastExecution": MockLastExecution(),
                            "isDisabled": 1,
                            "vendorId": "netapp",
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

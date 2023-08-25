"""
a collection of mock variables and methods
"""
import datetime
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

mock_managed_product = [
    type("managedProduct", (object,), {"lastExecution": datetime.datetime.utcnow() - datetime.timedelta(hours=10),
                                       "id": 1, "name": "FortiGate FGT-60F", "isDisabled": 0,
                                       "vendorData": {"osVersions": ""}}
         )
]

mock_disabled_managed_product = [
    type("managedProduct", (object,), {"lastExecution": 1, "name": 'FortiGate FGT-60F', "isDisabled": 1}),
]

mock_just_processed_managed_product = [
    type("managedProduct", (object,), {"lastExecution": datetime.datetime.utcnow() - datetime.timedelta(hours=3),
                                       "name": 'FortiGate FGT-60F', "isDisabled": 0}),
]

mock_formatted_bugs = [
    {
        "id": 1,
        "bugId": "510508",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues",
        "bug_urls": {
            "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues":
                datetime.datetime.utcnow() - datetime.timedelta(days=1)
        },
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nFortiManager "
                       "cannot assign multiple ADOMs to an admin user via JSON API.\n\nInformation from FortiManager "
                       "v6.4.5 release notes:\nProduct Element: AP Manager\nFortiManager cannot assign multiple ADOMs "
                       "to an admin user via JSON API.\n\nthe earliest recollection of this bug is traced back to Fort"
                       "iManager v6.4.5 released in February 22, 2021.\n\nThis bug is fixed in version 7.0.2 released "
                       "in October 20, 2021:\nProduct Element: AP Manager\nFortiManager cannot assign multiple ADOMs to"
                       " an admin user via JSON API.\n\nFor more information:\nhttps://docs.fortinet.com/document/forti"
                       "manager/6.4.5/release-notes/454729/known-issues\nhttps://docs.fortinet.com/document/fortimanage"
                       "r/7.0.1/release-notes/454729/known-issues\nhttps://docs.fortinet.com/document/fortimanager/7.0."
                       "2/release-notes/972111/resolved-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV7"
                      ".0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nFortiManager cannot assign multiple ADOMs to an admin user via JSON "
                   "API.",
        "status": None,
        "knownAffectedReleases": "6.4.5,7.0.1",
        "knownFixedReleases": "7.0.2",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-10-20 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 2,
        "bugId": "538057",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known-issues",
        "bug_urls": {
            "https://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known-issues":
                datetime.datetime.utcnow() - datetime.timedelta(days=1)
        },
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nThe OR\" "
                       "button in column filter may not work.\n\nInformation from FortiManager v6.4.5 release notes:\n"
                       "Product Element: AP Manager\nThe \"OR\" button in column filter may not work.\n\nthe earliest "
                       "recollection of this bug is traced back to FortiManager v6.4.5 released in February 22, 2021.\n"
                       "\nFor more information:\nhttps://docs.fortinet.com/document/fortimanager/6.4.5/release-notes/4"
                       "54729/known-issues\nhttps://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729"
                       "/known-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nThe \"OR\" button in column filter may not work.",
        "status": None,
        "knownAffectedReleases": "6.4.5,7.0.1",
        "knownFixedReleases": "",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-07-15 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 52,
        "bugId": "721783",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues",
        "bug_urls": {
            "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues":
                datetime.datetime.utcnow() - datetime.timedelta(days=1)
        },
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nApplying "
                       "Authentication or Portal Mapping changes may take several minutes.\n\nthe earliest "
                       "recollection of this bug is traced back to FortiManager v7.0.1 released in July 15, 2021.\n\n"
                       "This bug is fixed in version 7.0.2 released in October 20, 2021:\nProduct Element: AP Manager\n"
                       "Applying Authentication or Portal Mapping changes may take several minutes.\n\nFor more "
                       "information:\nhttps://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known"
                       "-issues\nhttps://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-is"
                       "sues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nApplying Authentication or Portal Mapping changes may take several "
                   "minutes.",
        "status": None,
        "knownAffectedReleases": "7.0.1",
        "knownFixedReleases": "7.0.2",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-10-20 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 53,
        "bugId": "722924",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues",
        "bug_urls": {
            "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues":
                datetime.datetime.utcnow() - datetime.timedelta(days=1)
        },
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nFortiManager "
                       "may not be able to edit skip-check-for-unsupported-os enable under SSL portal profile.\n\nthe "
                       "earliest recollection of this bug is traced back to FortiManager v7.0.1 released in July 15, "
                       "2021.\n\nThis bug is fixed in version 7.0.2 released in October 20, 2021:\nProduct Element: "
                       "AP Manager\nFortiManager may not be able to edit skip-check-for-unsupported-os enable under "
                       "SSL portal profile.\n\nFor more information:\nhttps://docs.fortinet.com/document/fortimanager/"
                       "7.0.1/release-notes/454729/known-issues\nhttps://docs.fortinet.com/document/fortimanager/7.0.2"
                       "/release-notes/972111/resolved-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nFortiManager may not be able to edit skip-check-for-unsupported-os "
                   "enable under SSL portal profile.",
        "status": None,
        "knownAffectedReleases": "7.0.1",
        "knownFixedReleases": "7.0.2",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-10-20 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 54,
        "bugId": "723447",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known-issues",
        "bug_urls": {
            "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues":
                datetime.datetime.utcnow() - datetime.timedelta(days=1)
        },
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nAfter "
                       "ADOM upgrade, install may fail due to wildcard FQDN type firewall address for Microsoft update."
                       "\n\nthe earliest recollection of this bug is traced back to FortiManager v7.0.1 released in "
                       "July 15, 2021.\n\nFor more information:\nhttps://docs.fortinet.com/document/fortimanager/7.0.1/"
                       "release-notes/454729/known-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nAfter ADOM upgrade, install may fail due to wildcard FQDN type "
                   "firewall address for Microsoft update.",
        "status": None,
        "knownAffectedReleases": "7.0.1",
        "knownFixedReleases": "",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-07-15 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    }
]
mock_formatted_mandatory_fields_missing = [
    {
        "id": 1,
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues",
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nFortiManager "
                       "cannot assign multiple ADOMs to an admin user via JSON API.\n\nInformation from FortiManager "
                       "v6.4.5 release notes:\nProduct Element: AP Manager\nFortiManager cannot assign multiple ADOMs "
                       "to an admin user via JSON API.\n\nthe earliest recollection of this bug is traced back to Fort"
                       "iManager v6.4.5 released in February 22, 2021.\n\nThis bug is fixed in version 7.0.2 released "
                       "in October 20, 2021:\nProduct Element: AP Manager\nFortiManager cannot assign multiple ADOMs to"
                       " an admin user via JSON API.\n\nFor more information:\nhttps://docs.fortinet.com/document/forti"
                       "manager/6.4.5/release-notes/454729/known-issues\nhttps://docs.fortinet.com/document/fortimanage"
                       "r/7.0.1/release-notes/454729/known-issues\nhttps://docs.fortinet.com/document/fortimanager/7.0."
                       "2/release-notes/972111/resolved-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV7"
                      ".0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nFortiManager cannot assign multiple ADOMs to an admin user via JSON "
                   "API.",
        "status": None,
        "knownAffectedReleases": "6.4.5,7.0.1",
        "knownFixedReleases": "7.0.2",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-10-20 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 2,
        "bugId": "538057",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nThe \"OR\" button in column filter may not work.",
        "status": None,
        "knownAffectedReleases": "6.4.5,7.0.1",
        "knownFixedReleases": "",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-07-15 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 52,
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues",
        "description": "Information from FortiManager v7.0.1 release notes:\nProduct Element: AP Manager\nApplying "
                       "Authentication or Portal Mapping changes may take several minutes.\n\nthe earliest "
                       "recollection of this bug is traced back to FortiManager v7.0.1 released in July 15, 2021.\n\n"
                       "This bug is fixed in version 7.0.2 released in October 20, 2021:\nProduct Element: AP Manager\n"
                       "Applying Authentication or Portal Mapping changes may take several minutes.\n\nFor more "
                       "information:\nhttps://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known"
                       "-issues\nhttps://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-is"
                       "sues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nApplying Authentication or Portal Mapping changes may take several "
                   "minutes.",
        "status": None,
        "knownAffectedReleases": "7.0.1",
        "knownFixedReleases": "7.0.2",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-10-20 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 53,
        "bugId": "722924",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.2/release-notes/972111/resolved-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nFortiManager may not be able to edit skip-check-for-unsupported-os "
                   "enable under SSL portal profile.",
        "status": None,
        "knownAffectedReleases": "7.0.1",
        "knownFixedReleases": "7.0.2",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-10-20 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    },
    {
        "id": 54,
        "bugId": "723447",
        "bugUrl": "https://docs.fortinet.com/document/fortimanager/7.0.1/release-notes/454729/known-issues",
        "snCiFilter": "install_status=1^operational_status=1^hardware_os_versionLIKEv7.0.1^NQhardware_os_versionLIKEV"
                      "7.0.1",
        "priority": "unspecified",
        "snCiTable": "cmdb_ci_firewall_device_fortinet",
        "summary": "Product Element: AP Manager\nAfter ADOM upgrade, install may fail due to wildcard FQDN type "
                   "firewall address for Microsoft update.",
        "status": None,
        "knownAffectedReleases": "7.0.1",
        "knownFixedReleases": "",
        "knownAffectedHardware": None,
        "knownAffectedOs": None,
        "vendorData": {"vendorProductName": "FortiGate FGT-60F"},
        "versions": None,
        "vendorCreatedDate": None,
        "vendorLastUpdatedDate": "2021-07-15 00:00:00",
        "processed": 0,
        "createdAt": "2021-10-28 15:56:34",
        "updatedAt": "2021-10-28 15:56:34",
        "managedProductId": 239,
        "vendorId": "fortinet"
    }
]

mock_sn_ci_query_response_json = [
    {"operational_status": "1",
     "short_description": "null\n\nFortinet FGT_60F, HW Serial#: FGT60FTK20007722\nSystem OID: 1.3.6.1.4.1.12356.10",
     "firmware_version": "v7.0.1,build0157,210714 (GA)", "serial_number": "FGT60FTK20007722",
     "hardware_os_version": "v7.0.1,build0157,210714 (GA)", "sys_id": "a74375e71b93b41027026351b24bcb70"}
]

mock_sn_ci_query_response_json_w_2_cis = [
    {"operational_status": "1",
     "short_description": "null\n\nFortinet FGT_60F, HW Serial#: FGT60FTK20007722\nSystem OID: 1.3.6.1.4.1.12356.10",
     "firmware_version": "v7.0.1,build0157,210714 (GA)", "serial_number": "FGT60FTK20007722",
     "hardware_os_version": "v7.0.1,build0157,210714 (GA)", "sys_id": "a74375e71b93b41027026351b24bcb70"},
    {"operational_status": "1",
     "short_description": "null\n\nFortinet FGT_60F, HW Serial#: FGT60FTK20007722\nSystem OID: 1.3.6.1.4.1.12356.10",
     "firmware_version": "v7.0.2,build0157,210714 (GA)", "serial_number": "FGT60FTK20007722",
     "hardware_os_version": "v7.0.2,build0157,210714 (GA)", "sys_id": "a74375e71b93b41027026351b24bcb70"}
]
mock_sn_ci_query_response_json_empty_description_field = [
    {"short_description": "", "sn_query_url": "test", "sys_id": "test"}
]

mock_sn_ci_query_response_json_empty_hardware_os_field = [
    {"short_description": "null\n\nFortinet FGT_60F, HW Serial#: FGT60FTK20007722\nSystem OID: 1.3.6.1.4.1.12356.10",
     "sn_query_url": "test", "sys_id": "test", "hardware_os_version": ""}
]

mock_sn_ci_query_response_json_missing_hardware_os_field = [
    {"short_description": "null\n\nFortinet FGT_60F, HW Serial#: FGT60FTK20007722\nSystem OID: 1.3.6.1.4.1.12356.10",
     "sn_query_url": "test", "sys_id": "test"}
]

mock_sn_ci_query_response_json_missing_description_field = [
    {"sn_query_url": "test", "sys_id": "test"}
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


class MockFortinetApiClient:
    """
    :return:
    """
    def __init__(
            self,
            vendor_id="fortinet"
    ):
        """
        """
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = dict()
        self.logger = logger
        self.service_now_ci_table = ""
        self.sn_query_cache = {}
        self.sn_versions = []
        self.vendor_id = vendor_id
        self.thread_error_tracker = 0

    @staticmethod
    def strip_html_spans(_html_string):
        return _html_string

    @staticmethod
    def timestamp_format(_time_str):
        return datetime.datetime.now()


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
    raise ConnectionError("Vendor integration error - fortinet data APIs are not working properly")


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
                             "all": lambda *_args: mock_managed_product,
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
                        "vendorId": "fortinet"
                    }
                ),
                "": type(
                        "mockClass", (object,),
                        {
                            "name": "test",
                            "lastExecution": MockLastExecution(),
                            "isDisabled": 1,
                            "vendorId": "fortinet",
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

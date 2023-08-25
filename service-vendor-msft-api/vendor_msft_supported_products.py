"""
  a list of supported products for sn sync
  Attributes:
      - name: BZ representation of the product
      - id: Microsoft official product name
      - service_now_table: sn table to search for CI
      - sysparm_query: queries to get product CI
  """
sql_server_products = [  # pragma: no cover
    {
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
    },
    {
        "id": "SQL Server 2017",
        "name": "SQL Server 2017",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH14.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/kb4047329-sql-server-2017-build-versions-"
            "346e8fcd-c07c-5eeb-e10b-e3411ba8d8dd"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build": "./td[2]/p/text()",
            "kb_url": "./td[6]/p/a/@href",
            "kb_id": "./td[6]/p/a/text()",
            "build_name": "./td[1]/p/text()",
            "release_date": './td[last()]/p/text()'
        }
    },
    {
        "id": "SQL Server 2016",
        "name": "SQL Server 2016",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH13.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/kb3177312-sql-server-2016-build-versions-"
            "d6cd8e5f-4aa3-20ac-f38f-8faef950840f"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build_name": "./td[1]/p/text()",
            "build": "./td[2]/p/text()",
            "kb_url": "./td[3]/p/a/@href",
            "kb_id": "./td[3]/p/a/text()",
            "release_date": './td[last()]/p/text()'
        }
    },
    {
        "id": "SQL Server 2014",
        "name": "SQL Server 2014",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH12.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/kb2936603-sql-server-2014-build-versions-"
            "6f75da99-d86f-53fa-23ce-3d2b4825eccb"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build": "./td[2]/p/text()",
            "kb_url": "./td[3]/p/a/@href",
            "kb_id": "./td[3]/p/a/text()",
            "build_name": "./td[1]/p/text()",
            "release_date": './td[last()]/p/text()'
        }
    },
    {
        "id": "SQL Server 2012",
        "name": "SQL Server 2012",
        "service_now_table": "cmdb_ci_db_mssql_instance",
        "sysparm_query": "versionSTARTSWITH11.0.",
        "type": "SQL Server",
        "build_urls": [
            "https://support.microsoft.com/en-us/topic/the-sql-server-2012-builds-that-were-released-after-sql-server-"
            "2012-was-released-5e586bab-f47b-60c8-ef1e-ede3104f28dc",
            "https://support.microsoft.com/en-us/topic/kb2772858-the-sql-server-2012-builds-that-were-released-after-"
            "sql-server-2012-service-pack-1-was-released-eadfd4ae-64d0-05eb-3742-ceaf5df975e4",
            "https://support.microsoft.com/en-us/topic/kb2983249-sql-server-2012-sp2-build-versions-"
            "2df8ef67-599a-b846-f0f8-c0193ea0ebad",
            "https://support.microsoft.com/en-us/topic/kb3133750-sql-server-2012-sp3-build-versions-"
            "a2566e34-4930-8204-1e29-a7d61ad2373a"
        ],
        "xpaths": {
            "kb_rows": "//*[contains(@class,'banded')]/tbody/tr",
            "build": "./td[2]/p/text()",
            "kb_url": "./td[3]/p/a/@href",
            "kb_id": "./td[3]/p/a/text()",
            "build_name": "./td[1]/p/text()",
            "release_date": './td[last()]/p/text()'
        }
    }
]

windows_server_products = [  # pragma: no cover
    {
        "id": "Windows Server 2022", "name": "Windows Server 2022", "service_now_table": "cmdb_ci_computer",
        "sysparm_query": "osLIKEWindows 2022^os_versionSTARTSWITH10.0.20348", "type": "Windows Server",
    },
    {
        "id": "Windows Server, version 20H2", "name": "Windows Server v20H2 (2019)", "type": "Windows Server",
        "service_now_table": "cmdb_ci_computer", "sysparm_query": "osLIKEWindows 2019^os_versionSTARTSWITH10.0.19042",
    },
    {
        "id": "Windows Server, version 2004", "name": "Windows Server v2004 (2019)", "type": "Windows Server",
        "service_now_table": "cmdb_ci_computer", "sysparm_query": "osLIKEWindows 2019^os_versionSTARTSWITH10.0.19041"
    },
    {
        "id": "Windows Server, version 1909",  "name": "Windows Server v1909 (2019)", "type": "Windows Server",
        "service_now_table": "cmdb_ci_computer", "sysparm_query": "osLIKEWindows 2019^os_versionSTARTSWITH10.0.18",
    },
    {
        "id": "Windows Server 2019", "name": "Windows Server 2019", "type": "Windows Server",
        "service_now_table": "cmdb_ci_computer", "sysparm_query": "osLIKEWindows 2019^os_versionSTARTSWITH10.0.17",
    },
    {
        "id": "Windows Server 2016", "service_now_table": "cmdb_ci_computer", "name": "Windows Server 2016",
        "sysparm_query": "osLIKEWindows 2016^os_versionSTARTSWITH10.0.14", "type": "Windows Server",
    },
    {
        "id": "Windows Server 2012 R2", "service_now_table": "cmdb_ci_computer", "name": "Windows Server 2012 R2",
        "sysparm_query": "osLIKEWindows 2012^os_versionSTARTSWITH6.3.96", "type": "Windows Server",
    },
    {
        "id": "Windows Server 2012", "service_now_table": "cmdb_ci_computer", "name": "Windows Server 2012",
        "sysparm_query": "osLIKEWindows 2012^os_versionSTARTSWITH6.2.92", "type": "Windows Server",
    },
    {
        "id": "Windows Server 2008 R2 SP1", "service_now_table": "cmdb_ci_computer", "type": "Windows Server",
        "name": "Windows Server 2008 R2 SP1", "sysparm_query": "osLIKEWindows 2008^os_versionSTARTSWITH6.1.7601.",
    },
    {
        "id": "Windows Server 2008 SP2", "service_now_table": "cmdb_ci_computer", "name": "Windows Server 2008 SP2",
        "sysparm_query": "osLIKEWindows 2008^os_versionSTARTSWITH6.0.6002", "type": "Windows Server",
    }
]

access_products = [
    {
        "id": "2019", "name": "Microsoft Access 2019", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "nameSTARTSWITHMicrosoft%20Access^versionSTARTSWITH17.", "type": "Microsoft Access",
        "xpaths": {
            "kb_urls": "//section[@class='ocpSection']//ul//a[contains(@class, 'ocpArticleLink')]",
        }
    },
    {
        "id": "2016", "name": "Microsoft Access 2016", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "nameSTARTSWITHMicrosoft%20Access^versionSTARTSWITH16.", "type": "Microsoft Access",
        "xpaths": {
            "kb_urls": "//section[@class='ocpSection']//ul//a[contains(@class, 'ocpArticleLink')]",
        }
    },
    {
        "id": "2013", "name": "Microsoft Access 2013", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "nameSTARTSWITHMicrosoft%20Access^versionSTARTSWITH15.", "type": "Microsoft Access",
        "xpaths": {
            "kb_urls": "//section[@class='ocpSection']//ul//a[contains(@class, 'ocpArticleLink')]",
        }
    },
    {
        "id": "2010", "name": "Microsoft Access 2010", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "nameSTARTSWITHMicrosoft%20Access^versionSTARTSWITH14.", "type": "Microsoft Access",
        "xpaths": {
            "kb_urls": "//section[@class='ocpSection']//ul//a[contains(@class, 'ocpArticleLink')]",
        }
    },
]

"""
  a list of supported products for sn sync
  Attributes:
      - classification: for redhat.bugzilla.com search queries
      - value:
              a. for redhat.bugzilla.com search queries
              b. managedProduct name
      - majorVersion: main version of vendorProduct
      - service_now_ci_table: sn table to search for CI
      - sysparm_fields: fields to return from sn
      - sysparm_query: queries to get product CI
      - id: Red Hat product id
  """

supported_products = [
            {
                "classification": "Red Hat",
                "value": "Red Hat Enterprise Linux 2.1",
                "id": "v111_product",
                "majorVersion": 2,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH2^osLIKERed Hat"
            },
            {
                "classification": "Red Hat",
                "value": "Red Hat Enterprise Linux 3",
                "id": "v121_product",
                "majorVersion": 3,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH3^osLIKERed Hat"

            },
            {
                "value": "Red Hat Enterprise Linux 4",
                "classification": "Red Hat",
                "id": "v131_product",
                "majorVersion": 4,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH4^osLIKERed Hat"

            },
            {
                "classification": "Red Hat",
                "id": "v141_product",
                "value": "Red Hat Enterprise Linux 5",
                "majorVersion": 5,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH5^osLIKERed Hat"
            },
            {
                "id": "v151_product",
                "classification": "Red Hat",
                "value": "Red Hat Enterprise Linux 6",
                "majorVersion": 6,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH6^osLIKERed Hat"

            },
            {
                "id": "v201_product",
                "classification": "Red Hat",
                "value": "Red Hat Enterprise Linux 7",
                "majorVersion": 7,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH7^osLIKERed Hat"
            },
            {
                "classification": "Red Hat",
                "id": "v370_product",
                "value": "Red Hat Enterprise Linux 8",
                "majorVersion": 8,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH8^osLIKERed Hat"
            },
            {
                "classification": "Red Hat",
                "id": "v604_product",
                "value": "Red Hat Enterprise Linux 9",
                "majorVersion": 9,
                "service_now_ci_table": "cmdb_ci_linux_server",
                "sysparm_fields": "os_version",
                "sysparm_query": "os_versionSTARTSWITH9^osLIKERed Hat"
            }
        ]

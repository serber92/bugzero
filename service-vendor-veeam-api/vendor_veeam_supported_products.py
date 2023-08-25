"""
  a list of supported products for sn sync
  Attributes:
      - name: Official Representation of the product
      - abbr: abbreviation used to search for kb in the vendor API
      - service_now_ci_table: sn table to search for CI
      - sysparm_fields: fields to return from sn
      - sysparm_query: queries to get product CI
  """
supported_products = [  # pragma: no cover
    {
        "abbr": "vbr", "name": "Veeam Backup & Replication", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",

    },
    {
        "abbr": "vaw", "name": "Veeam Agent for Microsoft Windows", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vbgcp", "name": "Veeam Backup for Google Cloud Platform", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vbo", "name": "Veeam Backup for Microsoft Office 365", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",

    },
    {
        "abbr": "vac", "name": "Veeam Service Provider Console", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vbrhv", "name": "Veeam Backup for Red Hat Virtualization", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "van", "name": "Veeam Backup for Nutanix AHV", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vbaws", "name": "Veeam Backup for AWS", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vbma", "name": "Veeam Backup for Microsoft Azure", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "one", "name": "Veeam ONE", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
     },
    {
        "abbr": "vace", "name": "Veeam Service Provider Console for the Enterprise",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "vmp", "name": "Veeam Management Pack for Microsoft System Center", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "vao", "name": "Veeam Disaster Recovery Orchestrator", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "cloud-connect", "name": "Veeam Cloud Connect", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "val", "name": "Veeam Agent for Linux", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "vpn", "name": "Veeam PN", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vam", "name": "Veeam Agent for Mac", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vaix", "name": "Veeam Agent for IBM AIX", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vaos", "name": "Veeam Agent for Oracle Solaris", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "vas", "name": "Veeam Availability Suite", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    },
    {
        "abbr": "vbof", "name": "Veeam Backup for Microsoft Office 365 Community Edition",
        "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1"
    },
    {
        "abbr": "fastscp", "name": "Veeam FastSCP", "service_now_table": "cmdb_ci_spkg",
        "sysparm_query": "install_status=1^operational_status=1",
    }
]

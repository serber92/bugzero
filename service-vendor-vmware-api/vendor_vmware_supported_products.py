"""
  a list of supported products for sn sync
  Attributes:
      - name: Official Representation of the product
      - service_now_ci_table: sn table to search for CI
      - sysparm_query: queries to get product CI
  """
supported_products = {  # pragma: no cover
    "ESXi": {
        "name": "ESXi", "service_now_table": "cmdb_ci_esx_server", "hosts": [], "versions": set()
    },
    "vCenter": {
        "name": "vCenter", "service_now_table": "cmdb_ci_vcenter", "hosts": [], "versions": set()
    }
}

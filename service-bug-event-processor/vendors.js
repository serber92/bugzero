module.exports = {
  aws: {
    vendorId: "aws",
    name: "AWS",
    priorities: [
      {
        label: "Issue",
        value: "Issue",
        bugValue: "Issue",
      },
      {
        label: "Account Notification",
        value: "Account Notification",
        bugValue: "Account Notification",
      },
      {
        label: "Scheduled Change",
        value: "Scheduled Change",
        bugValue: "Scheduled Change",
      },
    ],
    statuses: [
      {
        label: "Open",
        value: "Open",
      },
      {
        label: "Closed",
        value: "Closed",
      },
      {
        label: "Upcoming",
        value: "Upcoming",
      },
    ],
    eventScopes: [
      { label: "Public", value: "Public" },
      { label: "Account Specific", value: "Account Specific" },
    ],
  },
  hpe: {
    vendorId: "hpe",
    name: "HP Enterprise",
    type: "hardware",
    managedProductForm: {
      productLinkText:
        "Links ServiceNow CMDB products to BugZero supported products (e.g. HP DL380 Gen8)",
    },
    cmdb: {
      products: {
        sysparm_query:
          "status=In Production^manufacturer.name=HP^ORmanufacturer.name=Hewlett-Packard",
        sysparm_fields: "manufacturer,sys_id,display_name",
      },
    },
    priorities: [
      {
        label: "Customer Notice (Routine)",
        value: "cv66000024",
        bugValue: "CUSTOMER NOTICE",
      },
      {
        label: "Customer Advisory (Recommended)",
        value: "cv66000022",
        bugValue: "CUSTOMER ADVISORY",
      },
      {
        label: "Customer Bulletin (Critical)",
        value: "cv66000027",
        bugValue: "CUSTOMER BULLETIN",
      },
      {
        label: "Critical",
        value: "sev10000009",
        bugValue: "Critical",
      },
      {
        label: "Recommended",
        value: "sev10000001",
        bugValue: "Recommended",
      },
      {
        label: "Optional",
        value: "sev10000010",
        bugValue: "Optional",
      },
    ],
    statuses: [],
  },
  msft: {
    vendorId: "msft",
    name: "Microsoft",
    type: "software",
    managedProductForm: {
      productLinkText:
        "Links ServiceNow CMDB products to BugZero supported products (e.g. SQL Server)",
    },
    priorities: [
      {
        label: "Unspecified",
        value: "unspecified",
        bugValue: "unspecified",
      },
    ],
    statuses: [
      {
        label: "Windows Server: Reported",
        value: "Reported",
      },
      {
        label: "Windows Server: Investigating",
        value: "Investigating",
      },
      {
        label: "Windows Server: Confirmed",
        value: "Confirmed",
      },
      {
        label: "Windows Server: Mitigated",
        value: "Mitigated",
      },
      {
        label: "Windows Server: Mitigated: External",
        value: "Mitigated: External",
      },
      {
        label: "Windows Server: Resolved",
        value: "Resolved",
      },
      {
        label: "Windows Server: Resolved: External",
        value: "Resolved: External",
      },
    ],
  },
  msft365: {
    vendorId: "msft365",
    name: "Microsoft 365",
    type: "software",
    managedProductForm: {
      productLinkText:
        "Links ServiceNow CMDB products to BugZero supported products (e.g. SQL Server)",
    },
    priorities: [
      {
        label: "Incidents",
        value: "Incidents",
        bugValue: "Incidents",
      },
      {
        label: "Advisories",
        value: "Advisories",
        bugValue: "Advisories",
      },
    ],
    statuses : [
      {
        "label" : "Investigating",
        "value" : "Investigating"
      },
      {
        "label" : "Service degradation",
        "value" : "Service degradation"
      },
      {
        "label" : "Service interruption",
        "value" : "Service interruption"
      },
      {
        "label" : "Restoring service",
        "value" : "Restoring service"
      },
      {
        "label" : "Extended recovery",
        "value" : "Extended recovery"
      },
      {
        "label" : "Investigation suspended",
        "value" : "Investigation suspended"
      },
      {
        "label" : "Service restored",
        "value" : "Service restored"
      },
      {
        "label" : "False positive",
        "value" : "False positive"
      },
      {
        "label" : "Post-incident",
        "value" : "Post-incident"
      }
    ]
  },
  vmware: {
    vendorId: "vmware",
    name: "VMware",
    priorities: [
      {
        label: "Critical",
        value: "CRITICAL",
        bugValue: "CRITICAL",
      },
      {
        label: "Moderate",
        value: "MODERATE",
        bugValue: "MODERATE",
      },
      {
        label: "Trivial",
        value: "TRIVIAL",
        bugValue: "TRIVIAL",
      },
    ],
    statuses: [],
  },
  rh: {
    vendorId: "rh",
    name: "Red Hat",
    type: "software",
    managedProductForm: {
      productLinkText:
        "Links ServiceNow CMDB products to BugZero supported products (e.g. Redhat Enterprise Linux 8)",
    },
    cmdb: {
      products: {
        sysparm_query: "install_status=1^operational_status=1^osLIKELinux",
        sysparm_fields: "os,os_version",
      },
    },
    priorities: [
      {
        label: "Unspecified",
        value: "unspecified",
        bugValue: "unspecified",
      },
      {
        label: "Low",
        value: "low",
        bugValue: "low",
      },
      {
        label: "Medium",
        value: "medium",
        bugValue: "medium",
      },
      {
        label: "High",
        value: "high",
        bugValue: "high",
      },
      {
        label: "Urgent",
        value: "urgent",
        bugValue: "urgent",
      },
    ],
    statuses: [
      {
        label: "Assigned",
        value: "ASSIGNED",
      },
      {
        label: "Closed",
        value: "CLOSED",
      },
      {
        label: "Modified",
        value: "MODIFIED",
      },
      {
        label: "New",
        value: "NEW",
      },
      {
        label: "Verified",
        value: "VERIFIED",
      },
    ],
    resolutions: [
      {
        label: "Deferred",
        value: "DEFERRED",
      },
      {
        label: "Current Release",
        value: "CURRENTRELEASE",
      },
      {
        label: "Rawhide",
        value: "RAWHIDE",
      },
      {
        label: "Errata",
        value: "ERRATA",
      },
      {
        label: "Upstream",
        value: "UPSTREAM",
      },
      {
        label: "Next Release",
        value: "NEXTRELEASE",
      },
    ],
  },
  cisco: {
    vendorId: "cisco",
    name: "Cisco",
    type: "hardware",
    managedProductForm: {
      productLinkText:
        "Links ServiceNow CMDB products to BugZero supported products (e.g. Cisco Catalyst 6500)",
    },
    cmdb: {
      products: {
        sysparm_query:
          "install_status=1^operational_status=1^manufacturerLIKECisco^ORshort_descriptionLIKECisco",
        sysparm_fields: "manufacturer,sys_id,display_name,sys_class_name",
      },
      ciWithSerialNumber: {
        table: "cmdb_ci",
        sysparm_query:
          "install_status=1^operational_status=1^manufacturerLIKECisco^ORshort_descriptionLIKECisco^serial_numberISNOTEMPTY",
        sysparm_fields: "manufacturer,sys_id,display_name,serial_number",
      },
    },
    priorities: [
      {
        label: "Catastrophic",
        value: "1",
        bugValue: "1",
      },
      {
        label: "Severe",
        value: "2",
        bugValue: "2",
      },
      {
        label: "Moderate",
        value: "3",
        bugValue: "3",
      },
      {
        label: "Minor",
        value: "4",
        bugValue: "4",
      },
      {
        label: "Cosmetic",
        value: "5",
        bugValue: "5",
      },
      {
        label: "Enhancement",
        value: "6",
        bugValue: "6",
      },
    ],
    statuses: [
      {
        label: "Open",
        value: "O",
      },
      {
        label: "Fixed",
        value: "F",
      },
      {
        label: "Terminated",
        value: "T",
      },
    ],
  },
  fortinet: {
    vendorId: "fortinet",
    name: "Fortinet",
    type: "hardware",
    priorities: [
      {
        label: "Unspecified",
        value: "unspecified",
        bugValue: "unspecified",
      },
    ],
    statuses: [
      {
        label: "Fixed",
        value: "Fixed",
      },
      {
        label: "Open",
        value: "Open",
      },
    ],
  },
  veeam: {
    vendorId: "veeam",
    name: "Veeam",
    type: "hardware",
    priorities: [
      {
        label: "Unspecified",
        value: "unspecified",
        bugValue: "unspecified",
      },
    ],
    statuses: [],
  },
  netapp: {
    vendorId: "netapp",
    name: "NetApp",
    type: "hardware",
    priorities: [
      {
        label: "High",
        value: "high",
        bugValue: "high",
      },
      {
        label: "Medium",
        value: "medium",
        bugValue: "medium",
      },
      {
        label: "Low",
        value: "low",
        bugValue: "low",
      },
      {
        label: "Best Practices",
        value: "bestPractices",
        bugValue: "bestPractices",
      },
    ],
    statuses: [],
  },
  mongodb: {
    vendorId: "mongodb",
    name: "MongoDB",
    type: "software",
    managedProductForm: {
      productLinkText:
        "Links ServiceNow CMDB products to BugZero supported products (e.g. MongoDB Server)",
    },
    cmdb: {
      products: {
        sysparm_query:
          "install_status=1^operational_status=1^manufacturerLIKEMongo^ORshort_descriptionLIKEMongo",
        sysparm_fields: "manufacturer,sys_id,display_name,sys_class_name",
      },
    },
    priorities: [
      {
        label: "Blocker - P1",
        value: "Blocker - P1",
        bugValue: "Blocker - P1",
      },
      {
        label: "Critical - P2",
        value: "Critical - P2",
        bugValue: "Critical - P2",
      },
      {
        label: "Major - P3",
        value: "Major - P3",
        bugValue: "Major - P3",
      },
      {
        label: "Minor - P4",
        value: "Minor - P4",
        bugValue: "Minor - P4",
      },
      {
        label: "Trivial - P5",
        value: "Trivial - P5",
        bugValue: "Trivial - P5",
      },
    ],
    statuses: [
      {
        label: "Closed",
        value: "Closed",
      },
      {
        label: "Resolved",
        value: "Resolved",
      },
    ],
    resolutions: [
      { label: "Fixed", value: "Fixed" },
      { label: "Won't Fix", value: "Won't Fix" },
      { label: "Done", value: "Done" },
    ],
  },
};

"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"cisco","name":"Cisco","type":"hardware","managedProductForm":{"productLinkText":"Links ServiceNow CMDB products to BugZero supported products (e.g. Cisco Catalyst 6500)"},"cmdb":{"products":{"sysparm_query":"install_status=1^operational_status=1^manufacturerLIKECisco^ORshort_descriptionLIKECisco","sysparm_fields":"manufacturer,sys_id,display_name,sys_class_name"},"ciWithSerialNumber":{"table":"cmdb_ci","sysparm_query":"install_status=1^operational_status=1^manufacturerLIKECisco^ORshort_descriptionLIKECisco^serial_numberISNOTEMPTY","sysparm_fields":"manufacturer,sys_id,display_name,serial_number"}},"priorities":[{"label":"Catastrophic","value":"1","bugValue":"1"},{"label":"Severe","value":"2","bugValue":"2"},{"label":"Moderate","value":"3","bugValue":"3"},{"label":"Minor","value":"4","bugValue":"4"},{"label":"Cosmetic","value":"5","bugValue":"5"},{"label":"Enhancement","value":"6","bugValue":"6"}],"statuses":[{"label":"Open","value":"O"},{"label":"Fixed","value":"F"},{"label":"Terminated","value":"T"}]}\' WHERE id=\'cisco\''
    ),
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"hpe","name":"HPE","type":"hardware","managedProductForm":{"productLinkText":"Links ServiceNow CMDB products to BugZero supported products (e.g. HP DL380 Gen8)"},"cmdb":{"products":{"sysparm_query":"manufacturerLIKEHP^ORmanufacturerLIKEHewlett-Packard^ORmanufacturerLIKEHewlett Packard","sysparm_fields":"manufacturer,sys_id,display_name"}},"priorities":[{"label":"Customer Notice (Routine)","value":"cv66000024","bugValue":"CUSTOMER NOTICE"},{"label":"Customer Advisory (Recommended)","value":"cv66000022","bugValue":"CUSTOMER ADVISORY"},{"label":"Customer Bulletin (Critical)","value":"cv66000027","bugValue":"CUSTOMER BULLETIN"}],"statuses":[]}\' WHERE id=\'hpe\''
    ),
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"vmware","name":"VMware","type":"software","priorities":[{"label":"Critical","value":"CRITICAL","bugValue":"CRITICAL"},{"label":"Moderate","value":"MODERATE","bugValue":"MODERATE"},{"label":"Trivial","value":"TRIVIAL","bugValue":"TRIVIAL"}],"statuses":[]}\' WHERE id=\'vmware\''
    ),
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"mongodb","name":"MongoDB","type":"software","managedProductForm":{"productLinkText":"Links ServiceNow CMDB products to BugZero supported products (e.g. MongoDB Server)"},"cmdb":{"products":{"sysparm_query":"install_status=1^operational_status=1^manufacturerLIKEMongo^ORshort_descriptionLIKEMongo","sysparm_fields":"manufacturer,sys_id,display_name,sys_class_name"}},"priorities":[{"label":"Blocker - P1","value":"Blocker - P1","bugValue":"Blocker - P1"},{"label":"Critical - P2","value":"Critical - P2","bugValue":"Critical - P2"},{"label":"Major - P3","value":"Major - P3","bugValue":"Major - P3"},{"label":"Minor - P4","value":"Minor - P4","bugValue":"Minor - P4"},{"label":"Trivial - P5","value":"Trivial - P5","bugValue":"Trivial - P5"}],"statuses":[{"label":"Closed","value":"Closed"},{"label":"Resolved","value":"Resolved"}],"vendorResolutionStatuses":["Fixed","Won\\\'t Fix","Done"]}\' WHERE id=\'mongodb\''
    ),
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"rh","name":"Red Hat","type":"software","managedProductForm":{"productLinkText":"Links ServiceNow CMDB products to BugZero supported products (e.g. Redhat Enterprise Linux 8)"},"cmdb":{"products":{"sysparm_query":"install_status=1^operational_status=1^osLIKELinux","sysparm_fields":"os,os_version"}},"priorities":[{"label":"Unspecified","value":"unspecified","bugValue":"unspecified"},{"label":"Low","value":"low","bugValue":"low"},{"label":"Medium","value":"medium","bugValue":"medium"},{"label":"High","value":"high","bugValue":"high"},{"label":"Urgent","value":"urgent","bugValue":"urgent"}],"statuses":[{"label":"Assigned","value":"ASSIGNED"},{"label":"Closed","value":"CLOSED"},{"label":"Modified","value":"MODIFIED"},{"label":"New","value":"NEW"},{"label":"Verified","value":"VERIFIED"}]}\' WHERE id=\'rh\''
    ),
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"msft","name":"Microsoft","type":"software","managedProductForm":{"productLinkText":"Links ServiceNow CMDB products to BugZero supported products (e.g. SQL Server)"},"priorities":[{"label":"Unspecified","value":"unspecified","bugValue":"unspecified"}],"statuses":[]}\' WHERE id=\'msft\''
    ),

    /**
     * Add altering commands here.
     *
     * Example:
     * await queryInterface.createTable('users', { id: Sequelize.INTEGER });
     */
  ],

  down: async (queryInterface, Sequelize) => {
    /**
     * Add reverting commands here.
     *
     * Example:
     * await queryInterface.dropTable('users');
     */
  },
};

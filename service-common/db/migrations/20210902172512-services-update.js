"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => {
    const { sequelize } = queryInterface;
    try {
      await sequelize.transaction(async (transaction) => {
        const options = { transaction };
        await sequelize.query("SET FOREIGN_KEY_CHECKS = 0", options);
        await sequelize.query("TRUNCATE TABLE services", options);
        await sequelize.query("TRUNCATE TABLE serviceExecutions", options);
        await queryInterface.changeColumn(
          "serviceExecutions",
          "serviceId",
          {
            type: Sequelize.STRING,
            allowNull: false,
          },
          options
        );

        await sequelize.query("SET FOREIGN_KEY_CHECKS = 1", options);
        await queryInterface.bulkInsert("services", [
          {
            id: "vendor-cisco-bug-service",
            name: "Cisco Bug Service",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:19:59",
            updatedAt: "2021-09-01 22:19:59",
            vendorId: "cisco",
          },
          {
            id: "vendor-cisco-sync-service",
            name: "Cisco Sync",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:17:28",
            updatedAt: "2021-09-01 22:17:28",
            vendorId: "cisco",
          },
          {
            id: "vendor-hpe-bug-service",
            name: "HPE Bug Service",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:11:17",
            updatedAt: "2021-09-01 22:11:17",
            vendorId: "hpe",
          },
          {
            id: "vendor-hpe-sync-service",
            name: "HPE Sync",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:10:11",
            updatedAt: "2021-09-01 22:10:11",
            vendorId: "hpe",
          },
          {
            id: "vendor-msft-bug-processor",
            name: "MSFT Bug Processor",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 23:07:01",
            updatedAt: "2021-09-01 23:07:01",
            vendorId: "msft",
          },
          {
            id: "vendor-msft-bug-service",
            name: "MSFT Bug Service",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 23:05:37",
            updatedAt: "2021-09-01 23:05:37",
            vendorId: "msft",
          },
          {
            id: "vendor-msft-product-service",
            name: "MSFT Product Service",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:38:34",
            updatedAt: "2021-09-01 22:38:34",
            vendorId: "msft",
          },
          {
            id: "vendor-msft-rss-parser-service",
            name: "MSFT RSS Parser",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:33:07",
            updatedAt: "2021-09-01 22:33:07",
            vendorId: "msft",
          },
          {
            id: "vendor-msft-sync-service",
            name: "MSFT Sync",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:36:55",
            updatedAt: "2021-09-01 22:36:55",
            vendorId: "msft",
          },
          {
            id: "vendor-vmware-bug-service",
            name: "VMware Bug Service",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:15:02",
            updatedAt: "2021-09-01 22:15:02",
            vendorId: "vmware",
          },
          {
            id: "vendor-vmware-sync-service",
            name: "VMware Sync",
            status: "PENDING",
            message: null,
            vendorData: null,
            lastExecution: null,
            lastSuccess: null,
            lastError: null,
            enabled: 1,
            createdAt: "2021-09-01 22:14:12",
            updatedAt: "2021-09-01 22:14:12",
            vendorId: "vmware",
          },
        ]);
      });
    } catch (error) {
      console.log(error);
    }

    /**
     * Add altering commands here.
     *
     * Example:
     * await queryInterface.createTable('users', { id: Sequelize.INTEGER });
     */
  },

  down: async (queryInterface, Sequelize) => {
    /**
     * Add reverting commands here.
     *
     * Example:
     * await queryInterface.dropTable('users');
     */
  },
};

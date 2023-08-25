module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.createTable("services", {
      // Schema
      id: {
        type: Sequelize.STRING,
        primaryKey: true,
      },
      name: {
        type: Sequelize.STRING,
        allowNull: false,
      },
      status: {
        type: Sequelize.STRING,
        allowNull: false,
      },
      message: {
        type: Sequelize.STRING,
        allowNull: true,
      },
      vendorData: {
        type: Sequelize.JSON,
        allowNull: true,
      },
      lastExecution: {
        type: Sequelize.DATE,
        allowNull: true,
        defaultValue: null,
      },
      lastSuccess: {
        type: Sequelize.DATE,
        allowNull: true,
        defaultValue: null,
      },
      lastError: {
        type: Sequelize.DATE,
        allowNull: true,
        defaultValue: null,
      },
      enabled: {
        type: Sequelize.BOOLEAN,
        allowNull: true,
        defaultValue: true,
      },
      createdAt: {
        allowNull: false,
        type: Sequelize.DATE,
      },
      updatedAt: {
        allowNull: false,
        type: Sequelize.DATE,
      },
      vendorId: {
        type: Sequelize.STRING,
        allowNull: true,
      },
    }),
    await queryInterface.addIndex("services", ["vendorId"]),
    await queryInterface.createTable("serviceExecutions", {
      // Schema
      id: {
        type: Sequelize.INTEGER,
        autoIncrement: true,
        primaryKey: true,
      },
      startedAt: {
        type: Sequelize.DATE,
        allowNull: false,
      },
      endedAt: {
        type: Sequelize.DATE,
        allowNull: false,
      },
      error: {
        type: Sequelize.BOOLEAN,
        defaultValue: false,
        allowNull: true,
      },
      errorMessage: {
        type: Sequelize.STRING(1000),
        allowNull: true,
      },
      createdAt: {
        allowNull: false,
        type: Sequelize.DATE,
      },
      updatedAt: {
        allowNull: false,
        type: Sequelize.DATE,
      },
      vendorId: {
        type: Sequelize.STRING,
        allowNull: true,
      },
      serviceId: {
        type: Sequelize.INTEGER,
        allowNull: false,
      },
    }),
    await queryInterface.addIndex("serviceExecutions", ["serviceId"]),
    await queryInterface.addIndex("serviceExecutions", ["vendorId"]),
    await queryInterface.bulkInsert("services", [
      {
        id: "vendor-rh-api",
        name: "Red Hat",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        vendorId: "rh",
        createdAt: new Date(),
        updatedAt: new Date(),
      },
      {
        id: "vendor-cisco-callhome-api",
        name: "Cisco",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        vendorId: "cisco",
        createdAt: new Date(),
        updatedAt: new Date(),
      },
      {
        id: "bugzero-rest-api",
        name: "BugZero API",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      },
      {
        id: "bug-event-processor",
        name: "ServiceNow Sync",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      },
      {
        id: "vendor-hpe-api",
        name: "HPE",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        vendorId: "hpe",
        createdAt: new Date(),
        updatedAt: new Date(),
      },
      {
        id: "vendor-msft-api",
        name: "Microsoft",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        vendorId: "msft",
        createdAt: new Date(),
        updatedAt: new Date(),
      },
      {
        id: "managed-product-sync",
        name: "Managed Product Sync",
        status: "PENDING",
        message: null,
        vendorData: null,
        lastExecution: null,
        lastSuccess: null,
        lastError: null,
        enabled: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    ]),
  ],
  down: () => {
    /*
      Add reverting commands here.
      Return a promise to correctly handle asynchronicity.
      Example:
      return queryInterface.dropTable('users');
    */
  },
};

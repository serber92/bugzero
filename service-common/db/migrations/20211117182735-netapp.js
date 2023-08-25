module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "vendor-netapp-bug-svc",
        name: "NetApp Bug Service",
        status: "PENDING",
        vendorId: "netapp",
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
    await queryInterface.bulkInsert("vendors", [
      {
        id: "netapp",
        name: "NetApp",
        vendorData: JSON.stringify({
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
        }),
        active: 1,
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

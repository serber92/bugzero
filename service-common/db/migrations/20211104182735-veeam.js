module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "veeam-bugs-svc",
        name: "Veeam Bug Service",
        status: "PENDING",
        vendorId: "veeam",
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
        id: "veeam",
        name: "Veeam",
        vendorData: JSON.stringify({
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

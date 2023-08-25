module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "fortinet-bugs-svc",
        name: "Fortinet Bug Service",
        status: "PENDING",
        vendorId: "fortinet",
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
        id: "fortinet",
        name: "Fortinet",
        vendorData: JSON.stringify({
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

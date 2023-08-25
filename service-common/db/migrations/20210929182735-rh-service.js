module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "vendor-rh-bug-service",
        name: "Red Hat Bug Service",
        status: "PENDING",
        vendorId: "rh",
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

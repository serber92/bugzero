module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "msft365-bug-svc",
        name: "MSFT 365 Bug Service",
        status: "PENDING",
        vendorId: "msft365",
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
        id: "msft365",
        name: "Microsoft 365",
        vendorData: JSON.stringify({
          vendorId: "msft365",
          name: "Microsoft 365",
          priorities: [
            {
              label: "Advisories",
              value: "Advisories",
              bugValue: "Advisories",
            },
            {
              label: "Incidents",
              value: "Incidents",
              bugValue: "Incidents",
            },
          ],
          statuses: [
            {
              label: "Investigating",
              value: "Investigating",
            },
            {
              label: "Service degradation",
              value: "Service degradation",
            },
            {
              label: "Service interruption",
              value: "Service interruption",
            },
            {
              label: "Restoring service",
              value: "Restoring service",
            },
            {
              label: "Extended recovery",
              value: "Extended recovery",
            },
            {
              label: "Investigation suspended",
              value: "Investigation suspended",
            },
            {
              label: "Service restored",
              value: "Service restored",
            },
            {
              label: "False positive",
              value: "False positive",
            },
            {
              label: "Post-incident",
              value: "Post-incident",
            },
          ],
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

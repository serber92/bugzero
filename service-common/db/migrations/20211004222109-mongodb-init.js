module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "mongodb-bug-svc",
        name: "MongoDB Bug Service",
        status: "PENDING",
        vendorId: "mongodb",
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
        id: "mongodb",
        name: "MongoDB",
        vendorData: JSON.stringify({
          vendorId: "mongodb",
          name: "MongoDB",
          type: "software",
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

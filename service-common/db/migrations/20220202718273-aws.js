module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.bulkInsert("services", [
      {
        id: "aws-bug-svc",
        name: "AWS Bug Service",
        status: "PENDING",
        vendorId: "aws",
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
        id: "aws",
        name: "AWS",
        vendorData: JSON.stringify({
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

module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"vendorId":"msft","name":"Microsoft","priorities": [{  "label": "Unspecified",  "value": "unspecified",  "bugValue": "unspecified"}],"statuses": [{  "label": "Windows Server: Reported",  "value": "Reported"},{  "label": "Windows Server: Investigating",  "value": "Investigating"},{  "label": "Windows Server: Confirmed",  "value": "Confirmed"},{  "label": "Windows Server: Mitigated",  "value": "Mitigated"},{  "label": "Windows Server: Mitigated: External",  "value": "Mitigated: External"},{  "label": "Windows Server: Resolved",  "value": "Resolved"},{  "label": "Windows Server: Resolved: External",  "value": "Resolved: External"}]}\' WHERE id=\'msft\''
    ),
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

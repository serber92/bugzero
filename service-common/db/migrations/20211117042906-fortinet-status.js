"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.sequelize.query(
      'UPDATE vendors SET vendorData=\'{"name": "Fortinet", "type": "hardware", "statuses": [{"label": "Fixed","value": "Fixed"},{"label": "Open","value": "Open"}], "vendorId": "fortinet", "priorities": [{"label": "Unspecified", "value": "unspecified", "bugValue": "unspecified"}]}\' WHERE name=\'fortinet\''
    ),

    /**
     * Add altering commands here.
     *
     * Example:
     * await queryInterface.createTable('users', { id: Sequelize.INTEGER });
     */
  ],

  down: async (queryInterface, Sequelize) => {
    /**
     * Add reverting commands here.
     *
     * Example:
     * await queryInterface.dropTable('users');
     */
  },
};

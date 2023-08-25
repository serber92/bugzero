"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.sequelize.query(
      'UPDATE vendors SET name="VMware" WHERE id="vmware"'
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

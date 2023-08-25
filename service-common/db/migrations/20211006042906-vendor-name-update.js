"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => [
    await queryInterface.sequelize.query(
      "UPDATE vendors SET name='Cisco' WHERE name='cisco'"
    ),
    await queryInterface.sequelize.query(
      "UPDATE vendors SET name='HPE' WHERE name='hpe'"
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

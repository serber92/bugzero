require("dotenv").config();

module.exports = {
  development: {
    username: process.env.DATABASE_USER,
    password: process.env.DATABASE_PASSWORD,
    database: process.env.DATABASE_DB,
    host: process.env.DATABASE_HOST,
    dialect: "mysql",
    dialectOptions: {
      connectTimeout: 60000,
    },
  },
  test: {
    username: process.env.DATABASE_USER,
    password: process.env.DATABASE_PASSWORD,
    database: process.env.DATABASE_TEST_DB,
    host: process.env.DATABASE_HOST,
    dialect: "mysql",
    dialectOptions: {
      connectTimeout: 60000,
    },
  },
  production: {
    username: process.env.DATABASE_USER,
    password: process.env.DATABASE_PASSWORD,
    database: process.env.DATABASE_DB,
    host: process.env.DATABASE_HOST,
    dialect: "mysql",
    dialectOptions: {
      connectTimeout: 60000,
    },
  },
};

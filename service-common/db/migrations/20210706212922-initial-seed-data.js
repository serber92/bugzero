const path = require("path");
const util = require("util");
const childProc = require("child_process");
const {
  DATABASE_USER,
  DATABASE_PASSWORD,
  DATABASE_DB,
  DATABASE_HOST,
  DATABASE_PORT,
} = process.env;
const exec = util.promisify(childProc.exec);
const filePath = path.parse(__filename).dir;
const sqlPath = path.join(filePath, "..", "sql", "bootstrap.sql");

async function mysqlImport() {
  const { stdout, stderr } = await exec(
    `mysql -u ${DATABASE_USER} -p${DATABASE_PASSWORD} -h ${DATABASE_HOST} ${DATABASE_DB} -P ${DATABASE_PORT} < "${sqlPath}"`
  );
  console.log("stdout:", stdout);
  console.log("stderr:", stderr);
}

module.exports = {
  up: async () => {
    const result = await mysqlImport();
    return result;
  },
  down: () => {
    /*
      Add reverting commands here.
      Return a promise to correctly handle asynchronicity.
      Example:
      return queryInterface.dropTable('users');
    */
  },
};

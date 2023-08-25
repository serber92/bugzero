const glob = require('glob');
const path = require('path');
const Sequelize = require('sequelize')
// const NoteModel = require('./models/Note')
console.log('Init');
console.log(process.env);
const sequelize = new Sequelize(
  process.env.DB_NAME,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    dialect: 'mysql',
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT)
  }
)
console.log('Done.');


const basename = path.basename(__filename);
  console.log('dir', process.cwd())
  // This file will cycle through all models in the directory and initialize them
  const models = {};
  const files = glob.sync('**/*.model.js', {
    // cwd: `${process.cwd()}/db/models`,
  });
  files.forEach((file) => {
    if (file !== basename) {
      const model = require(path.join(__dirname, file))(sequelize, Sequelize.DataTypes)

      // const model = sequelize.import(path.join(__dirname, file));
      models[model.name] = model;
    }
  });

  Object.keys(models).forEach((modelName) => {
    if (models[modelName].associate) {
      models[modelName].associate(models);
    }
  });

  models.Sequelize = sequelize.Sequelize;
  models.sequelize = sequelize;

// const Note = NoteModel(sequelize, Sequelize)
// const Models = { Note }
const connection = {}

module.exports = async () => {
  console.log('check connection');
  if (connection.isConnected) {
    console.log('=> Using existing connection.')
    return models;

  }
  console.log('Sync..');
  // console.log('models', models);
  // console.log('Databases truncated');
  // remove the migration db
  // await sequelize.drop();
  // await sequelize.query('DROP TABLE IF EXISTS SequelizeMeta;');

  await sequelize.sync()
  console.log('Auth..');

  await sequelize.authenticate()
  connection.isConnected = true
  console.log('=> Created a new connection.')
  return models
}

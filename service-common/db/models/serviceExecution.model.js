module.exports = (sequelize, DataTypes) => {
  const serviceExecutionModel = sequelize.define("serviceExecution", {
    // Schema
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    startedAt: {
      type: DataTypes.DATE,
      allowNull: false,
    },
    endedAt: {
      type: DataTypes.DATE,
      allowNull: false,
    },
    error: {
      type: DataTypes.BOOLEAN,
      defaultValue: false,
      allowNull: true,
    },
    errorMessage: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
  });

  serviceExecutionModel.associate = (models) => {
    models.serviceExecution.belongsTo(models.service);
    models.serviceExecution.belongsTo(models.vendor);
    // models.serviceExecution.belongsTo(models.serviceExecution);
    // models.serviceExecution.belongsTo(models.serviceExecutionVersion);
  };

  return serviceExecutionModel;
};

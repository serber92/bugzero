module.exports = (sequelize, DataTypes) => {
  const serviceModel = sequelize.define("service", {
    // Schema
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    status: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    message: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    vendorData: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    lastExecution: {
      type: DataTypes.DATE,
      allowNull: true,
      defaultValue: null,
    },
    lastSuccess: {
      type: DataTypes.DATE,
      allowNull: true,
      defaultValue: null,
    },
    lastError: {
      type: DataTypes.DATE,
      allowNull: true,
      defaultValue: null,
    },
    enabled: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: true,
    },
  });

  serviceModel.associate = (models) => {
    models.service.belongsTo(models.vendor);
    // models.service.belongsTo(models.service);
    // models.service.belongsTo(models.serviceVersion);
  };

  return serviceModel;
};

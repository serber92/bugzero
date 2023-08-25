module.exports = (sequelize, DataTypes) => {
  const managedProductModel = sequelize.define("managedProduct", {
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
    snProductId: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    vendorPriorities: {
      type: DataTypes.JSON,
      allowNull: false,
    },
    vendorStatuses: {
      type: DataTypes.JSON,
      allowNull: false,
    },
    lastExecution: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    vendorData: {
      type: DataTypes.JSON,
      allowNull: true,
    },

    isDisabled: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: false,
    },
  });

  managedProductModel.associate = (models) => {
    models.managedProduct.belongsTo(models.vendor);
    models.managedProduct.hasMany(models.bug);
    models.managedProduct.belongsTo(models.vendorProductFamily);
    models.managedProduct.belongsTo(models.vendorProduct);
    models.managedProduct.belongsToMany(models.vendorProductVersion,{ through: 'managedProductVersions' });
  };

  return managedProductModel;
};

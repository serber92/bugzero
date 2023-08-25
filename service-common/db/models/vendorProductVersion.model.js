module.exports = (sequelize, DataTypes) => {
  const vendorProductVersionModel = sequelize.define("vendorProductVersion", {
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
    productUrl: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
    snCiFilter: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
    snCiTable: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    productVersionId: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    vendorData: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    active: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: true,
    },
  });

  vendorProductVersionModel.associate = (models) => {
    models.vendorProductVersion.belongsTo(models.vendorProduct);
    models.vendorProductVersion.belongsTo(models.vendor);
    models.vendorProductVersion.belongsToMany(models.managedProduct,{ through: 'managedProductVersions' });

    // models.vendorProductVersion.belongsTo(models.vendorProductVersionFamily);
    // models.vendorProductVersion.belongsTo(models.vendorProductVersion);
    // models.vendorProductVersion.belongsTo(models.vendorProductVersionVersion);
  };

  return vendorProductVersionModel;
};

module.exports = (sequelize, DataTypes) => {
  const vendorProductModel = sequelize.define("vendorProduct", {
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
    productId: {
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

  vendorProductModel.associate = (models) => {
    models.vendorProduct.belongsTo(models.vendorProductFamily);
    models.vendorProduct.belongsTo(models.vendor);
    models.vendorProduct.hasMany(models.managedProduct);
    models.vendorProduct.hasMany(models.vendorProductVersion);
    models.vendorProduct.belongsTo(models.vendorProductFamily);
    // models.vendorProduct.belongsTo(models.vendorProduct);
    // models.vendorProduct.belongsTo(models.vendorProductVersion);
  };

  return vendorProductModel;
};

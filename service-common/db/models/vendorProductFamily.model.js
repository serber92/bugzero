module.exports = (sequelize, DataTypes) => {
  const vendorProductFamilyModel = sequelize.define("vendorProductFamily", {
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
    // productUrl: {
    //   type: DataTypes.STRING,
    //   allowNull: true,
    // },
    productFamilyId: {
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

  vendorProductFamilyModel.associate = (models) => {
    models.vendorProductFamily.belongsTo(models.vendor);
    models.vendorProductFamily.hasMany(models.vendorProduct);
    // models.vendorProductFamily.belongsTo(models.vendorProductFamilyFamily);
    // models.vendorProductFamily.belongsTo(models.vendorProductFamily);
    // models.vendorProductFamily.belongsTo(models.vendorProductFamilyVersion);
  };

  return vendorProductFamilyModel;
};

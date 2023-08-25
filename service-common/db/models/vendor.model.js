module.exports = (sequelize, DataTypes) => {
  const vendorModel = sequelize.define("vendor", {
    // Schema
    id: {
      // hpe, cisco
      type: DataTypes.STRING,
      primaryKey: true,
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    vendorData: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    active: {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: true,
    },
  });

  vendorModel.associate = () => {
    // models.vendor.hasM(models.bug);
    // models.vendor.belongsTo(models.vendorProductFamily);
    // models.vendor.belongsTo(models.vendorProduct);
    // models.vendor.belongsTo(models.vendorProductVersion);
  };

  return vendorModel;
};

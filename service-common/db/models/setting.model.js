module.exports = (sequelize, DataTypes) => {
  const settingModel = sequelize.define("setting", {
    // Schema
    id: {
      // cisco
      type: DataTypes.STRING,
      primaryKey: true,
    }, // ENUM (global, vendor)
    type: {
      type: DataTypes.STRING,
      allowNull: false,
    }, // Object { daysBack: 60}
    value: {
      type: DataTypes.JSON,
      allowNull: false,
    },
  });
  settingModel.associate = (models) => {
    // models.setting.hasOne(models.bug);
    // models.setting.belongsTo(models.vendorProductFamily);
    // models.setting.belongsTo(models.vendorProduct);
    // models.setting.belongsTo(models.vendorProductVersion);
  };

  return settingModel;
};

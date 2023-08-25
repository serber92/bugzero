module.exports = (sequelize, DataTypes) => {
  const bugModel = sequelize.define("bug", {
    // Schema
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    bugId: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    bugUrl: {
      type: DataTypes.STRING(1000),
      allowNull: false,
    },
    description: {
      type: DataTypes.TEXT,
      allowNull: false,
    },
    priority: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    snCiFilter: {
      type: DataTypes.STRING(1000),
      allowNull: false,
    },
    snCiTable: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    summary: {
      type: DataTypes.STRING(500),
      allowNull: false,
    },
    status: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    knownAffectedReleases: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
    knownFixedReleases: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
    knownAffectedHardware: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
    // discuss
    knownAffectedOs: {
      type: DataTypes.STRING(1000),
      allowNull: true,
    },
    vendorData: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    versions: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    vendorCreatedDate: {
      type: DataTypes.DATE,
    },
    vendorLastUpdatedDate: {
      type: DataTypes.DATE,
    },
    processed: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: false,
    },
  });

  bugModel.associate = (models) => {
    models.bug.belongsTo(models.managedProduct);
    models.bug.belongsTo(models.vendor);
  };

  return bugModel;
};

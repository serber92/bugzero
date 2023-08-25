module.exports = (sequelize, DataTypes) => {
  const msftBugModel = sequelize.define("msftBug", {
    // Schema
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    kbUrl: {
      type: DataTypes.STRING(1000),
      allowNull: false,
    },
    vendorCreatedDate: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    vendorLastUpdatedDate: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    guid: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    kbId: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    knownAffectedReleases: {
      type: DataTypes.JSON,
      allowNull: true,
    },
    rssFeedId: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    rssFeedName: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    apiUrl: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    eolProject: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    heading: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    title: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    description: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    processed: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: false,
    },
    processError: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: false,
    },
    processErrorMsg: {
      type: DataTypes.STRING(500),
      allowNull: true,
      defaultValue: "",
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
      type: DataTypes.STRING(300),
      allowNull: false,
    },
    status: {
      type: DataTypes.STRING,
      allowNull: true,
    },
  });

  msftBugModel.associate = (models) => {
    models.msftBug.belongsTo(models.managedProduct);
    // models.msftBug.hasMany(models.subscription);
    // models.msftBug.hasMany(models.seenUser, {
    //   as: 'loggedInUser',
    //   foreignKey: {
    //     name: 'msftBugId',
    //     allowNull: false
    //   }
    // });
  };

  return msftBugModel;
};

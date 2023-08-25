"use strict";
// lib
const handler = require("../libs/handler-lib");
const moment = require("moment");

// AWS.config.update({ region: 'us-east-1' }); // temp
// var credentials = new AWS.SharedIniFileCredentials({ profile: 'bz-app' });
// AWS.config.credentials = credentials;

module.exports.get = handler(async (event, context, db) => {
  // Get Data for Dashboard
  // Vendor Service Status
  console.log("db", db);
  const servicesPromise = db.service.findAll({
    include: {
      model: db.vendor,
      where: {
        active: true,
      },
    },
  });
  // Bugs by Vendor and priority
  const bugsLast24HoursPromise = db.bug.findAll({
    where: {
      updatedAt: {
        [db.Sequelize.Op.gte]: moment().subtract(1, "days").toDate(),
      },
    },
    group: ["priority", "vendorId"],
    attributes: [
      "priority",
      "vendorId",
      [db.Sequelize.fn("COUNT", "priority"), "priorityCount"],
    ],
  });
  const bugsLastWeekPromise = db.bug.findAll({
    where: {
      updatedAt: {
        [db.Sequelize.Op.gte]: moment().subtract(7, "days").toDate(),
      },
    },
    group: ["priority", "vendorId"],
    attributes: [
      "priority",
      "vendorId",
      [db.sequelize.fn("COUNT", "priority"), "priorityCount"],
    ],
  });
  const bugsLastMonthPromise = db.bug.findAll({
    where: {
      updatedAt: {
        [db.Sequelize.Op.gte]: moment().subtract(1, "month").toDate(),
      },
    },
    group: ["priority", "vendorId"],
    attributes: [
      "priority",
      "vendorId",
      [db.sequelize.fn("COUNT", "priority"), "priorityCount"],
    ],
  });
  const bugsLastQuarterPromise = db.bug.findAll({
    where: {
      updatedAt: {
        [db.Sequelize.Op.gte]: moment().subtract(4, "months").toDate(),
      },
    },
    group: ["priority", "vendorId"],
    attributes: [
      "priority",
      "vendorId",
      [db.sequelize.fn("COUNT", "priority"), "priorityCount"],
    ],
  });

  const [
    services,
    bugsLast24Hours,
    bugsLastWeek,
    bugsLastMonth,
    bugsLastQuarter,
  ] = await Promise.all([
    servicesPromise,
    bugsLast24HoursPromise,
    bugsLastWeekPromise,
    bugsLastMonthPromise,
    bugsLastQuarterPromise,
  ]);
  const response = {
    services,
    bugsLast24Hours,
    bugsLastWeek,
    bugsLastMonth,
    bugsLastQuarter,
  };
  console.log("response", response);
  return response;
});

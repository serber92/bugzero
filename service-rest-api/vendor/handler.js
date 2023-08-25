"use strict";
// env
const httpStatus = require("http-status");
// lib
const APIError = require("../libs/APIError");
const handler = require("../libs/handler-lib");
const validator = require("../libs/validator");
const schemas = require("./schemas");

const { STAGE } = process.env;
const aws = require("aws-sdk");
const lambda = new aws.Lambda({
  region: "us-east-1", //change to your region
});

// AWS.config.update({ region: 'us-east-1' }); // temp
// var credentials = new AWS.SharedIniFileCredentials({ profile: 'bz-app' });
// AWS.config.credentials = credentials;

module.exports.get = handler(async (event, context, db) => {
  const vendorId = event.pathParameters.vendorId;
  if (!vendorId)
    throw new APIError("Missing vendor ID", httpStatus.BAD_REQUEST);

  const vendor = await db.vendor.findByPk(vendorId);
  return vendor;
});

module.exports.listVendors = handler(async (event, context, db) => {
  const vendors = await db.vendor.findAll();
  return vendors;
});
module.exports.testCreds = handler(async (event) => {
  // vendor-netapp-api-dev-netapp-test-creds
  const vendorId = event.pathParameters.vendorId;

  if (!vendorId)
    throw new APIError("Missing vendor ID", httpStatus.BAD_REQUEST);

  const { body } = event;
  const item = JSON.parse(body);
  if (!validator(schemas.testCredsBody, item))
    throw new APIError("Missing required data", httpStatus.BAD_REQUEST);

  const result = await lambda
    .invoke({
      FunctionName: `vendor-${vendorId}-api-${STAGE}-test-creds`,
      Payload: JSON.stringify(item, null, 2), // pass params
    })
    .promise();
  if (result && result.Payload) {
    console.log("result", result);
  }

  return JSON.parse(result.Payload);
});
module.exports.listProducts = handler(async (event, context, db) => {
  const vendorId = event.pathParameters.vendorId;
  if (!vendorId)
    throw new APIError("Missing vendor ID", httpStatus.BAD_REQUEST);

  const vendorProducts = await db.vendorProduct.findAll({
    where: {
      vendorId,
    },
  });
  return vendorProducts;
});

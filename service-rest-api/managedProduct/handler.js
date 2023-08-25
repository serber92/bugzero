"use strict";
const httpStatus = require("http-status");
const { SNS_SERVICE_TRIGGER_TOPIC_ARN } = process.env;
const { sendTopic } = require("../libs/sns-lib");
// lib
const handler = require("../libs/handler-lib");
const APIError = require("../libs/APIError");
const validator = require("../libs/validator");
const schemas = require("./schemas");

module.exports.list = handler(async (event, context, db) => {
  const vendorId = event.queryStringParameters.vendorId;
  if (!vendorId)
    throw new APIError("Missing vendor ID", httpStatus.BAD_REQUEST);

  // Fetch bugs based on params

  const products = await db.managedProduct.findAll({
    where: {
      vendorId,
    },
  });
  return products;
});

module.exports.get = handler(async (event, context, db) => {
  const managedProductId = event.pathParameters.id;
  if (!managedProductId)
    throw new APIError("Missing managed product ID", httpStatus.BAD_REQUEST);
  const managedProduct = await db.managedProduct.findByPk(managedProductId);

  return managedProduct;
});
// create or update
module.exports.createOrUpdate = handler(async (event, context, db) => {
  const { body } = event;
  const item = JSON.parse(body);
  if (!validator(schemas.createBody, item))
    throw new APIError("Missing required data", httpStatus.BAD_REQUEST);

  const vendorId = item.vendorId;
  if (item.id) {
    //update
    if (!item.isDisabled) item.lastExecution = null;
    const existingManagedProduct = await db.managedProduct.update(item, {
      where: { id: item.id },
    });
    if (!item.isDisabled) {
      // if Item is not disabled, trigger service
      console.log("Product is not disabled, trigger service");
      const params = {
        TopicArn: SNS_SERVICE_TRIGGER_TOPIC_ARN,
        Message: vendorId,
        MessageAttributes: {
          service: {
            DataType: "String",
            StringValue: `${vendorId}`,
          },
        },
      };
      await sendTopic(params);
    }
    return existingManagedProduct;
  } else {
    // create
    const newManagedProduct = db.managedProduct.build(item);
    await newManagedProduct.save();
    // Send Trigger vendor services
    const params = {
      TopicArn: SNS_SERVICE_TRIGGER_TOPIC_ARN,
      Message: vendorId,
      MessageAttributes: {
        service: {
          DataType: "String",
          StringValue: `${vendorId}`,
        },
      },
    };
    await sendTopic(params);
    return newManagedProduct;
  }
});

module.exports.del = handler(async (event, context, db) => {
  const managedProductId = event.pathParameters.id;
  if (!managedProductId)
    throw new APIError("Missing managed product ID", httpStatus.BAD_REQUEST);

  const managedProduct = await db.managedProduct.destroy({
    where: {
      id: managedProductId,
    },
  });
  // Delete bugs
  const bugs = await db.bug.destroy({
    where: {
      managedProductId,
    },
  });

  return {
    bugs,
    managedProduct,
  };
});

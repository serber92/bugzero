"use strict";
const httpStatus = require("http-status");
const handler = require("../libs/handler-lib");
const APIError = require("../libs/APIError");
const validator = require("../libs/validator");
const schemas = require("./schemas");
const uuid = require("uuid");
const AWS = require("aws-sdk");
const { sendTopic } = require("../libs/sns-lib");
const { SNS_SERVICE_TRIGGER_TOPIC_ARN } = process.env;
const secretsmanager = new AWS.SecretsManager({
  region: "us-east-1",
});

module.exports.getSetting = handler(async (event, context, db) => {
  const settingId = event.pathParameters.settingId;

  if (!settingId)
    throw new APIError("Missing setting ID", httpStatus.BAD_REQUEST);

  const setting = await db.setting.findByPk(settingId);
  if (!setting) return null;
  return setting.value;
});

module.exports.updateSetting = handler(async (event, context, db) => {
  const { body } = event;
  const settingId = event.pathParameters.settingId;
  let currentSettings = null;
  if (!settingId)
    throw new APIError("Missing setting ID", httpStatus.BAD_REQUEST);

  try {
    const item = JSON.parse(body);
    // item.id = settingId;
    console.log(
      "schemas.updateSettingBody, item",
      schemas.updateSettingBody,
      item
    );
    if (!validator(schemas.updateSettingBody, item))
      throw new APIError("Missing required data", httpStatus.BAD_REQUEST);

    try {
      currentSettings = (await db.setting.findByPk(settingId)).value;
    } catch (e) {
      console.log("No setting found.");
    }
    if (!currentSettings) {
      const newItem = {
        value: { ...item },
        id: settingId,
        type: item.type,
      };
      // Setting does not exist. Create it
      currentSettings = db.setting.build(newItem);
      await currentSettings.save();
    }

    console.log("currentSettings", currentSettings);

    // If vendor setting change, reset last execution on managed products
    if (currentSettings && item.type === "vendor") {
      console.log("vendor setting.");
      const vendorId = settingId;
      const settingsVendorSorted = Object.keys(currentSettings)
        .sort()
        .reduce((a, c) => ((a[c] = currentSettings[c]), a), {});
      const itemVendorSorted = Object.keys(item)
        .sort()
        .reduce((a, c) => ((a[c] = item[c]), a), {});

      if (
        JSON.stringify(settingsVendorSorted) !==
        JSON.stringify(itemVendorSorted)
      ) {
        // Vendor configuration was changed. Reset last execution on managed products
        // Get managed products
        const managedProducts = await db.managedProduct.findAll({
          where: {
            vendorId,
          },
        });
        for (let i = 0; i < managedProducts.length; i++) {
          const managedProduct = managedProducts[i];
          if (managedProduct.isDisabled) continue; // skip
          managedProduct.lastExecution = null;
          await managedProduct.save();
        }
        console.log(
          `${settingId} updated..reset managed products last execution`
        );
        // Trigger vendor services
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
        console.log("params", params);
        await sendTopic(params);
        console.log("Sent Topic");
      }
    }
    // Check for vendor changes

    console.log("finished");

    const results = await db.setting.update(
      { value: item },
      {
        where: {
          id: settingId,
        },
      }
    );
    return results;
  } catch (e) {
    console.log("e", e);
    throw new APIError("An error occurred", httpStatus.INTERNAL_SERVER_ERROR);
  }
});

module.exports.createOrUpdateClientSecret = handler(async (event) => {
  const { body } = event;
  try {
    const item = JSON.parse(body);
    console.log("item", item);
    const vendorId = item.vendorId;
    const key = item.key;
    const secret = JSON.stringify(item.secret);
    const secretId = `setting-${vendorId}-${key}`;
    const describeParams = {
      SecretId: secretId /* required */,
    };
    let describeSecret;
    try {
      describeSecret = await secretsmanager
        .describeSecret(describeParams)
        .promise();
    } catch (e) {
      console.error("Error finding secret", e);
    }
    if (describeSecret && describeSecret.ARN) {
      // secret exists
      console.log("Update secret");
      var params = {
        ClientRequestToken: uuid.v4(),
        SecretId: secretId,
        SecretString: secret,
      };
      console.log("update");
      const result = await secretsmanager.putSecretValue(params).promise();
      console.log("result", result);
      return result;
    } else {
      // secret does not exist
      console.log("Create secret");

      const params = {
        ClientRequestToken: uuid.v4(),
        Description: secretId,
        Name: secretId,
        SecretString: secret,
      };

      // create secret
      const result = await secretsmanager.createSecret(params).promise();
      console.log("result", result);
      return result;
    }
  } catch (e) {
    console.log(e);
    throw new APIError("Unable to create secret", httpStatus.BAD_REQUEST);
  }
});

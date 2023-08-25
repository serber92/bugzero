"use strict";
const httpStatus = require("http-status");
const handler = require("../libs/handler-lib");
const APIError = require("../libs/APIError");
const validator = require("../libs/validator");
const schemas = require("./schemas");
const axios = require("axios");
const { SN_SUPPORT_USER_BASIC_AUTH_KEY } = process.env;

module.exports.createSupportTicket = handler(async (event) => {
  try {
    const { body } = event;
    const item = JSON.parse(body);

    if (!validator(schemas.createSupportTicketBody, item))
      throw new APIError("Missing required data", httpStatus.BAD_REQUEST);

    const url = `https://portal.findbugzero.com/api/now/table/sn_customerservice_case`;
    const config = {
      headers: {
        Authorization: `Basic ${SN_SUPPORT_USER_BASIC_AUTH_KEY}`,
      },
      timeout: 15000,
    };
    const result = await axios.post(url, item, config);
    console.log(`🐛 [created support ticket}`, result);
  } catch (e) {
    console.error(e);
    throw new APIError(
      "Unable to create support ticket",
      httpStatus.INTERNAL_SERVER_ERROR
    );
  }

  /*

     data = {
      ARN: "arn:aws:secretsmanager:us-west-2:123456789012:secret:MyTestDatabaseSecret-a1b2c3",
      Name: "MyTestDatabaseSecret",
      VersionId: "EXAMPLE1-90ab-cdef-fedc-ba987SECRET1"
     }
     */
});

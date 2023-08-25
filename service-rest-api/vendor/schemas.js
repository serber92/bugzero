const Joi = require("joi");

const testCredsBody = Joi.object().unknown(true);

module.exports = { testCredsBody };

const Joi = require("joi");

const createBody = Joi.object()
  .keys({
    vendorId: Joi.string().required(),
  })
  .unknown(true);

module.exports = { createBody };

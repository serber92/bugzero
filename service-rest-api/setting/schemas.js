const Joi = require("joi");

const updateSettingBody = Joi.object()
  .keys({
    type: Joi.string().required(),
  })
  .unknown(true);

module.exports = { updateSettingBody };

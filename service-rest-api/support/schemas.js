const Joi = require("joi");

const createSupportTicketBody = Joi.object()
  .keys({
    watch_list: Joi.string().required(),
    short_description: Joi.string().required(),
    description: Joi.string().required(),
  })
  .unknown(true);

module.exports = { createSupportTicketBody };

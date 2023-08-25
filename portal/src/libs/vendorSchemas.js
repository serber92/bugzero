import Joi from 'joi';

const cisco = Joi.object().keys({
  daysBack: Joi.string().required(),
  apiClientId: Joi.string().required(),
  apiClientSecret: Joi.string().required()
});

const aws = Joi.object().keys({
  daysBack: Joi.string().required(),
  apiClientId: Joi.string().required(),
  apiClientSecret: Joi.string().required(),
  snCompanySysId: Joi.string().required(),
  awsApiHealthApiRoleArn: Joi.string().required()
});

const hpe = Joi.object().keys({
  daysBack: Joi.string().required()
});
const msft = Joi.object().keys({
  daysBack: Joi.string().required(),
  snCompanySysId: Joi.string().required()
});
const msft365 = Joi.object().keys({
  daysBack: Joi.string().required(),
  snCompanySysId: Joi.string().required()
});
const veeam = Joi.object().keys({
  daysBack: Joi.string().required(),
  snCompanySysId: Joi.string().required()
});
const netapp = Joi.object().keys({
  daysBack: Joi.string().required(),
  snCompanySysId: Joi.string().required()
});
const rh = Joi.object().keys({
  daysBack: Joi.string().required(),
  snCompanySysId: Joi.string().required()
});

const vmware = Joi.object().keys({
  snCompanySysId: Joi.string().required()
});
const fortinet = Joi.object().keys({
  snCompanySysId: Joi.string().required()
});
const mongodb = Joi.object().keys({
  daysBack: Joi.string().required(),
  snCompanySysId: Joi.string().required()
});

export const vendorSchemas = { msft365, aws, hpe, msft, cisco, rh, vmware, veeam, netapp, mongodb, fortinet };

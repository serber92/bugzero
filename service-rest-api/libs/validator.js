module.exports = function validate(schema, data) {
  console.log("schema", schema);
  console.log("data", data);
  const response = schema.validate(data);
  console.log("response", response);
  return !response.error;
};

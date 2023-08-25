const AWS = require("aws-sdk");

// AWS.config.update({ region: 'us-east-1' }); // temp
// var credentials = new AWS.SharedIniFileCredentials({ profile: 'bz-app' }); // temp
// AWS.config.credentials = credentials; // temp
const dynamoDb = new AWS.DynamoDB.DocumentClient();

function getItem(params) {
  return dynamoDb.get(params).promise();
}

function putItem(params) {
  return dynamoDb.put(params).promise();
}

function updateItem(params) {
  return dynamoDb.update(params).promise();
}

function query(params) {
  return dynamoDb.query(params).promise();
}

function scan(params) {
  return dynamoDb.scan(params).promise();
}

function unmarshall(data) {
  return AWS.DynamoDB.Converter.unmarshall(data);
}
module.exports = {
  putItem,
  query,
  updateItem,
  scan,
  getItem,
  unmarshall,
  dynamoDb,
};

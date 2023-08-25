const util = require("util");
const AWS = require("aws-sdk");

let logs;

// Log AWS SDK calls
AWS.config.logger = { log: debug };

function debug() {
  logs.push({
    date: new Date(),
    string: util.format.apply(null, arguments),
  });
}

function init(event) {
  logs = [];

  // Log API event
  debug("API event", {
    body: event.body,
    pathParameters: event.pathParameters,
    queryStringParameters: event.queryStringParameters,
  });
}

function flush(e) {
  logs.forEach(({ date, string }) => console.debug(date, string));
  console.error(e);
}

module.exports = {
  debug,
  init,
  flush,
};

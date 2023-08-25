const debug = require("./debug-lib");
const connectToDatabase = require("./db-lib"); // initialize connection
const STAGE = process.env.STAGE;

function handler(lambda) {
  return async function (event, context) {
    let body, statusCode;
    console.log("event", event);
    console.log("context", context);

    // Start debugger
    debug.init(event, context);
    try {
      // Run the Lambda
      const db = await connectToDatabase();

      console.log("Running lambda...");
      body = await lambda(event, context, db);
      body = JSON.stringify(body);
      console.log("Done running lambda...", body);
      statusCode = 200;
    } catch (e) {
      // Print debug messages
      console.error(e);
      debug.flush(e);
      body = { error: e.message };
      statusCode = e.status || 500;
    }

    if (STAGE === "dev") {
      return {
        statusCode,
        body,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Credentials": true,
        },
      };
    } else {
      return {
        statusCode,
        body,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Credentials": true,
        },
      };
    }
    // Return HTTP response
  };
}

module.exports = handler;

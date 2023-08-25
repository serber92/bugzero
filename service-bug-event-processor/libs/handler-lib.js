const debug = require("./debug-lib");
const connectToDatabase = require("./db-lib"); // initialize connection
const eventManagement = require("./eventManagement-lib");
function handler(lambda) {
  return async function (event, context) {
    let body, statusCode, timer;
    try {
      timer = setTimeout(() => {
        console.log("Detected timeout!", context.getRemainingTimeInMillis());
        eventManagement.sendEvent({
          message: "Lambda timeout",
        });

        // &c.
      }, context.getRemainingTimeInMillis() - 3000);
      // rest of code..
      console.log("event", event);
      console.log("context", context);
      const db = await connectToDatabase();

      // Start debugger
      debug.init(event, context);
      // Run the Lambda
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
      eventManagement.sendEvent(e);
      console.log("event", event);
    } finally {
      clearTimeout(timer);
    }

    // Return HTTP response
    return {
      statusCode,
      body,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    };
  };
}

module.exports = handler;

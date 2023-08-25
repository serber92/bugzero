const { SN_AUTH_EVENT_MANAGEMENT_BASIC_TOKEN, STAGE } = process.env;
const axios = require("axios");
async function sendEvent(error) {
  const body = {
    records: [
      {
        source: "bugzero",
        event_class: "bug-event-processor",
        resource: "bugEventProcessor",
        node: STAGE,
        metric_name: error.message,
        type: "operational",
        severity: "1",
        description: error.stack || error.message,
      },
    ],
  };
  const config = {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Basic ${SN_AUTH_EVENT_MANAGEMENT_BASIC_TOKEN}`,
    },
  };
  const response = await axios.post(
    "https://ven03949.service-now.com/api/global/em/jsonv2",
    body,
    config
  );
  return response;
}
module.exports = {
  sendEvent,
};

const { SNSClient, PublishCommand } = require("@aws-sdk/client-sns");

// Set the AWS Region.
const REGION = "us-east-1";
const snsClient = new SNSClient({ region: REGION });
// Create SNS service object.

async function sendTopic(params) {
  try {
    // const data = await snsClient.send(new SetTopicAttributesCommand(params));

    const command = new PublishCommand(params);
    const data = await snsClient.send(command);
    console.log("Success.", data);
    return data; // For unit tests.
  } catch (err) {
    console.log("Error", err.stack);
  }
}
module.exports = { sendTopic };

const AWS = require("aws-sdk");
const secretsManager = new AWS.SecretsManager({
  region: "us-east-1",
});

async function readSecret(secretName) {
  try {
    const data = await secretsManager
      .getSecretValue({
        SecretId: secretName,
      })
      .promise();

    if (data) {
      if (data.SecretString) {
        const secret = data.SecretString;
        const parsedSecret = JSON.parse(secret);
        return parsedSecret;
      }

      const binarySecretData = data.SecretBinary;
      return binarySecretData;
    } else return null;
  } catch (error) {
    console.log("Error retrieving secrets");
    console.log(error);
    return null;
  }
}
module.exports = {
  readSecret,
};

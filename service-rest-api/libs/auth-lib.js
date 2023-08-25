const AWS = require("aws-sdk");
const AmazonCognitoIdentity = require("amazon-cognito-identity-js");
global.fetch = require("node-fetch").default; // .default for webpack.
const USER_POOL_ID = process.env.USER_POOL_ID;
const USER_POOL_CLIENT_ID = process.env.USER_POOL_CLIENT_ID;

const poolData = {
  UserPoolId: USER_POOL_ID,
  ClientId: USER_POOL_CLIENT_ID,
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
async function assumeCognitoGroupRole(RoleArn) {
  const sts = new AWS.STS({ region: process.env.REGION });
  const stsParams = {
    RoleArn,
    RoleSessionName: "CognitoGroupSession",
    DurationSeconds: 3600,
  };
  const credentials = await sts.assumeRole(stsParams).promise();

  return credentials;
}
async function login(Username, Password) {
  var authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails({
    Username,
    Password,
  });

  var userData = {
    Username,
    Pool: userPool,
  };
  var cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

  return new Promise((resolve, reject) => {
    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: async (result) => {
        const tokens = {
          accessToken: result.getAccessToken().getJwtToken(),
          idToken: result.getIdToken().getJwtToken(),
          refreshToken: result.getRefreshToken().getToken(),
        };
        // Check if user is activated

        return resolve(tokens);
      },
      onFailure: (err) => {
        reject(err);
      },
    });
  });
}
module.exports = {
  login,
  assumeCognitoGroupRole,
};

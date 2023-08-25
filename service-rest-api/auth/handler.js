const httpStatus = require("http-status");
const auth = require("../libs/auth-lib");

module.exports.login = async (event) => {
  try {
    const { body } = event;
    const { user, pass } = JSON.parse(body);

    const tokens = await auth.login(user, pass);
    const response = {
      headers: {
        "content-type": "application/json",
      },
      statusCode: httpStatus.OK,
      body: JSON.stringify(tokens),
    };
    return response;
  } catch (e) {
    console.log("err", e);

    const response = {
      statusCode: httpStatus.UNAUTHORIZED,
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(e),
    };
    return response;
  }
};

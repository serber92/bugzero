const debugLib = require("../libs/debug-lib");
const authLib = require("../libs/auth-lib");
const handlerLib = require("../libs/handler-lib");
const APIError = require("../libs/APIError");

test("debug-lib helper methods defined and exported", () => {
  expect(debugLib.debug).toBeDefined();
  expect(debugLib.init).toBeDefined();
  expect(debugLib.flush).toBeDefined();
});
test("auth-lib helper methods defined and exported", () => {
  expect(authLib.login).toBeDefined();
  expect(authLib.assumeCognitoGroupRole).toBeDefined();
});
test("handler-lib helper methods defined and exported", () => {
  expect(handlerLib).toBeDefined();
});
test("APIError helper methods defined and exported", () => {
  expect(APIError).toBeDefined();
});

const debugLib = require("../libs/debug-lib");
const handlerLib = require("../libs/handler-lib");
const dbLib = require("../libs/db-lib");
test("debug-lib helper methods defined and exported", () => {
  expect(debugLib.debug).toBeDefined();
  expect(debugLib.init).toBeDefined();
  expect(debugLib.flush).toBeDefined();
});
test("handler-lib helper is exported", () => {
  expect(handlerLib).toBeDefined();
});
test("db helper is exported", () => {
  expect(dbLib).toBeDefined();
});

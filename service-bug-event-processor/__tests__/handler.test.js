const handler = require("../handler");

describe("handler.bugEventProcessor", () => {
  test("check existence", async () => {
    expect(handler.bugEventProcessor).toBeDefined();
    expect(typeof handler.bugEventProcessor).toBe("function");
  });
});

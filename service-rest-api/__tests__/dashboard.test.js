const dashboard = require("../dashboard/handler");
// enable mocking
// jest.enableAutomock();
const getEvent = {
  pathParameters: { dashboardId: "1" },
};
jest.mock("../libs/db-lib", () => {
  return () => {
    return Promise.resolve({
      sequelize: { fn: () => {} },
      Sequelize: {
        fn: () => {},
        Op: {
          gte: "gte",
        },
      },
      service: {
        findAll: () => {
          return Promise.resolve([
            {
              id: "test",
            },
          ]);
        },
      },
      bug: {
        findByPk: () => {
          return Promise.resolve({});
        },
        findAll: () => {
          return Promise.resolve([
            {
              id: "test",
            },
          ]);
        },
      },
      vendor: "",
    });
  };
});

describe("dashboard.get", () => {
  test("it should exist", async () => {
    expect(dashboard.get).toBeDefined();
  });

  test("it should get", async () => {
    expect(await dashboard.get(getEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});

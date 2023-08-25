const auth = require("../auth/handler");
const authLib = require("../libs/auth-lib");
// enable mocking
// jest.enableAutomock();

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

describe("auth.login", () => {
  test("it should exist", async () => {
    expect(auth.login).toBeDefined();
  });
});
describe("authLib.assumeCognitoGroupRole", () => {
  test("it should exist", async () => {
    expect(authLib.assumeCognitoGroupRole).toBeDefined();
  });
});

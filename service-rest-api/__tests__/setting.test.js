const setting = require("../setting/handler");
// enable mocking
// jest.enableAutomock();
const updateSettingEvent = {
  body: '{"type":"vendor","value":{"vendorStatuses":[],"vendorPriorities":[{"vendorPriority":"unspecified","snPriority":"1|1|1"}],"vendorId":"msft","isDisabled":false,"vendorProductVersionIds":[],"name":"Exchange/Sharepoint Server","vendorProductFamilyId":"90bedbeb-782d-7b46-9f4f-721cc5d647d6","snProductId":"90bedbeb-782d-7b46-9f4f-721cc5d647d6"},"id":1}',
  pathParameters: { settingId: "1" },
};
const updateErrorSettingEvent = {
  body: "{badjson",
  pathParameters: { settingId: "1" },
};
const createOrUpdateClientSecretEvent = {
  body: '{"vendorId": "msft","key":"key", "secret":{}}',
};

const getSettingEvent = {
  pathParameters: { settingId: "1" },
};

jest.mock("../libs/db-lib", () => {
  return () => {
    return Promise.resolve({
      managedProduct: {
        findAll: () => {
          return Promise.resolve([
            {
              save: () => Promise.resolve({}),
            },
          ]);
        },
      },
      setting: {
        findByPk: () => {
          return Promise.resolve({
            id: "id",
            type: "vendor",
            value: {
              vendorStatuses: ["test"],
              test: "example change",
            },
          });
        },
        findAll: () => {
          return Promise.resolve([]);
        },
        build: () => {
          return { save: () => Promise.resolve({}) };
        },
        update: () => {
          return { save: () => Promise.resolve({}) };
        },
        destroy: () => {
          return { save: () => Promise.resolve({}) };
        },
      },
    });
  };
});
jest.mock("aws-sdk", () => {
  return {
    config: {
      logger: {},
    },
    SecretsManager: function SecretsManager() {
      this.constructor = () => {};
      return {
        createSecret: () => {
          return {
            promise: () => {
              return Promise.resolve();
            },
          };
        },
        describeSecret: () => {
          return {
            promise: () => {
              return Promise.resolve();
            },
          };
        },
        putSecretValue: () => {
          return {
            promise: () => {
              return Promise.resolve();
            },
          };
        },
      };
    },
  };
});
// const db = {

// }
// jest.mock("db-lib");

describe("setting.getSetting", () => {
  test("it should exist", async () => {
    expect(setting.getSetting).toBeDefined();
  });

  test("it should getSetting", async () => {
    expect(await setting.getSetting(getSettingEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
  test("it should error", async () => {
    // Remove param
    getSettingEvent.pathParameters.settingId = null;
    expect(await setting.getSetting(getSettingEvent)).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});
describe("setting.updateSetting", () => {
  test("it should exist", async () => {
    expect(setting.updateSetting).toBeDefined();
  });
  test("it should update", async () => {
    // Remove param
    expect(await setting.updateSetting(updateSettingEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
  test("it should throw a 500", async () => {
    // Remove param
    expect(await setting.updateSetting(updateErrorSettingEvent)).toMatchObject({
      statusCode: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
  test("it should error", async () => {
    // Remove param
    updateSettingEvent.pathParameters.settingId = null;
    expect(await setting.updateSetting(updateSettingEvent)).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});
describe("setting.createOrUpdateClientSecret", () => {
  test("it should exist", async () => {
    expect(setting.createOrUpdateClientSecret).toBeDefined();
  });
  test("it should create", async () => {
    // Remove param
    expect(
      await setting.createOrUpdateClientSecret(createOrUpdateClientSecretEvent)
    ).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
  test("it should error", async () => {
    // Remove param
    createOrUpdateClientSecretEvent.body = null;
    expect(
      await setting.createOrUpdateClientSecret(createOrUpdateClientSecretEvent)
    ).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});

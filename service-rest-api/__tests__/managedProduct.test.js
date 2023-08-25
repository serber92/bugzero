const managedProduct = require("../managedProduct/handler");
// enable mocking
// jest.enableAutomock();
const updateEvent = {
  body: '{"vendorStatuses":[],"vendorPriorities":[{"vendorPriority":"unspecified","snPriority":"1|1|1"}],"vendorId":"msft","isDisabled":false,"vendorProductVersionIds":[],"name":"Exchange/Sharepoint Server","vendorProductFamilyId":"90bedbeb-782d-7b46-9f4f-721cc5d647d6","snProductId":"90bedbeb-782d-7b46-9f4f-721cc5d647d6","id":1}',
};
const createEvent = {
  body: '{"vendorStatuses":[],"vendorPriorities":[{"vendorPriority":"unspecified","snPriority":"1|1|1"}],"vendorId":"msft","isDisabled":false,"vendorProductVersionIds":[],"name":"Exchange/Sharepoint Server","vendorProductFamilyId":"90bedbeb-782d-7b46-9f4f-721cc5d647d6","snProductId":"90bedbeb-782d-7b46-9f4f-721cc5d647d6"}',
};
const getEvent = {
  pathParameters: { id: "1" },
};
const listEvent = {
  queryStringParameters: { vendorId: "msft" },
};
const delEvent = {
  pathParameters: { id: "1" },
};
jest.mock("../libs/db-lib", () => {
  return () => {
    return Promise.resolve({
      managedProduct: {
        findByPk: () => {
          return Promise.resolve({});
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
      bug: {
        findByPk: () => {
          return Promise.resolve({});
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
// const db = {

// }
// jest.mock("db-lib");
describe("managedProduct.list", () => {
  test("it should exist", async () => {
    expect(managedProduct.list).toBeDefined();
  });
  test("it should list", async () => {
    expect(await managedProduct.list(listEvent)).toMatchObject({
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
    listEvent.queryStringParameters.vendorId = null;
    expect(await managedProduct.list(listEvent)).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});
describe("managedProduct.get", () => {
  test("it should exist", async () => {
    expect(managedProduct.get).toBeDefined();
  });

  test("it should get", async () => {
    expect(await managedProduct.get(getEvent)).toMatchObject({
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
    getEvent.pathParameters.id = null;
    expect(await managedProduct.get(getEvent)).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});
describe("managedProduct.create", () => {
  test("it should exist", async () => {
    expect(managedProduct.create).toBeDefined();
  });
  test("it should update", async () => {
    // Remove param
    expect(await managedProduct.create(updateEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });

  test("it should create", async () => {
    expect(await managedProduct.create(createEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});
describe("managedProduct.del", () => {
  test("it should exist", async () => {
    expect(managedProduct.del).toBeDefined();
  });

  test("it should delete", async () => {
    expect(await managedProduct.del(delEvent)).toMatchObject({
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
    delEvent.pathParameters.id = null;
    expect(await managedProduct.del(delEvent)).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});
// test("should return a 200 with teh player if the palyer is valid", async () => {
//   const event = eventGenerator({
//     body: {
//       name: "tom",
//       score: 43,
//     },
//     pathParametersObject: {
//       ID: "jgugvcnje49",
//     },
//   });
//   const res = await createPlayerScore.handler(event);

//   expect(res.statusCode).toBe(200);
//   const body = JSON.parse(res.body);
//   expect(body).toEqual({
//     newUser: {
//       name: "tom",
//       score: 43,
//       ID: "jgugvcnje49",
//     },
//   });
// });

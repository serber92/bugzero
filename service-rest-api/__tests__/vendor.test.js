const vendor = require("../vendor/handler");
// enable mocking
// jest.enableAutomock();
const getEvent = {
  pathParameters: { vendorId: "1" },
};
const listEvent = {
  queryStringParameters: { vendorId: "msft" },
};
const listProductsEvent = {
  pathParameters: {
    vendorId: "msft",
  },
};
jest.mock("../libs/db-lib", () => {
  return () => {
    return Promise.resolve({
      vendorProduct: {
        findByPk: () => {
          return Promise.resolve({});
        },
        findAll: () => {
          return Promise.resolve([]);
        },
      },
      vendor: {
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

describe("vendor.get", () => {
  test("it should exist", async () => {
    expect(vendor.get).toBeDefined();
  });

  test("it should get", async () => {
    expect(await vendor.get(getEvent)).toMatchObject({
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
    getEvent.pathParameters.vendorId = null;
    expect(await vendor.get(getEvent)).toMatchObject({
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});

describe("vendor.listVendors", () => {
  test("it should exist", async () => {
    expect(vendor.listVendors).toBeDefined();
  });
  test("it should list", async () => {
    // Remove param
    expect(await vendor.listVendors(listEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });
});

describe("vendor.listProducts", () => {
  test("it should exist", async () => {
    expect(vendor.listProducts).toBeDefined();
  });
  test("it should list", async () => {
    // Remove param
    expect(await vendor.listProducts(listProductsEvent)).toMatchObject({
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    });
  });

  test("it should error", async () => {
    listProductsEvent.pathParameters.vendorId = null;
    expect(await vendor.listProducts(listProductsEvent)).toMatchObject({
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
//   const res = await listVendorsPlayerScore.handler(event);

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

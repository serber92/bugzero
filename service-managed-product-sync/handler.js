const axios = require("axios");
/* Local Debug */

// const VENDOR_PRODUCTS_TABLE = process.env.VENDOR_PRODUCTS_TABLE;
const PRODUCTS_TABLE = process.env.PRODUCTS_TABLE;
const SETTINGS_TABLE = process.env.SETTINGS_TABLE;
const VENDOR_PRODUCTS_TABLE = process.env.VENDOR_PRODUCTS_TABLE;
const VENDOR_PRODUCT_VERSIONS_TABLE = process.env.VENDOR_PRODUCT_VERSIONS_TABLE;

// lib
const db = require("./db");

module.exports.managedProductSync = async () => {
  try {
    // Fetch managed products
    const params = {
      TableName: PRODUCTS_TABLE,
      FilterExpression: "#vendorId = :vendorId",
      ExpressionAttributeNames: {
        "#vendorId": "vendorId",
      },
      ExpressionAttributeValues: {
        ":vendorId": "msft",
      },
    };
    // get all clients
    const settingsParams = {
      Key: {
        settingId: "servicenow",
      },
      TableName: SETTINGS_TABLE,
    };
    console.log("setting query", settingsParams);
    const { Item } = await db.getItem(settingsParams);
    const serviceNowSettings = Item;

    // console.log('clients', clients);

    // todo only get active records in query
    const products = (await db.scan(params)).Items;
    // console.log('products', products);
    for (let i = 0; i < products.length; i++) {
      const vendorProductVersionIds = [];
      const queryCache = {};
      let cacheCount = 0;
      const managedProduct = products[i];
      console.log("---------------------------");
      console.log(`Managed Product: ${managedProduct.name}`);
      console.log("---------------------------");
      console.log("");

      // Get Vendor Products by vendorProductFamilyId
      const vendorProductFamilyId = managedProduct.vendorProductFamilyId;
      const params = {
        TableName: VENDOR_PRODUCTS_TABLE,
        FilterExpression: "#vendorProductFamilyId = :vendorProductFamilyId",
        ExpressionAttributeNames: {
          "#vendorProductFamilyId": "vendorProductFamilyId",
        },
        ExpressionAttributeValues: {
          ":vendorProductFamilyId": vendorProductFamilyId,
        },
      };
      const vendorProducts = (await db.scan(params)).Items;
      for (let i = 0; i < vendorProducts.length; i++) {
        const vendorProduct = vendorProducts[i];
        // Get all versions for each product.
        const params = {
          TableName: VENDOR_PRODUCT_VERSIONS_TABLE,
          FilterExpression: "#vendorProductId = :vendorProductId",
          ExpressionAttributeNames: {
            "#vendorProductId": "vendorProductId",
          },
          ExpressionAttributeValues: {
            ":vendorProductId": vendorProduct.vendorProductId,
          },
        };
        const vendorProductVersions = (await db.scan(params)).Items;
        console.log(``);
        console.log(`# Vendor Product: ${vendorProduct.name}`);
        console.log(`# Versions: ${vendorProductVersions.length}`);
        console.log(``);

        // console.log('vendorProductVersions:', vendorProductVersions.length);
        for (let i = 0; i < vendorProductVersions.length; i++) {
          // Query SN for matching affected CI's
          const { snCiTable, snCiFilter, name, vendorProductVersionId } =
            vendorProductVersions[i];
          if (!snCiFilter || !snCiTable) {
            console.log(`[❌] ${name} - Missing Filter or Table. Skipping...`);

            continue; // skip
          }
          const query = `${snCiTable}?sysparm_query=${snCiFilter}&sysparm_fields=null`;
          let count = null;
          // If the same query has already been executed, load count.
          if (queryCache[query]) {
            count = queryCache[query];
            console.log(`[${count}] (Cached) ${name}`);
            cacheCount++;
          } else {
            // get Count
            const url = `${
              serviceNowSettings.snApiUrl
            }/api/now/table/${encodeURI(query)}`;
            console.log(`URL: ${url}`);
            const response = await axios.get(url, {
              headers: {
                Authorization: `Basic ${serviceNowSettings.snAuthToken}`,
              },
            });
            // console.log('response', response.headers);
            count = parseInt(response.headers["x-total-count"]);
            // Cache query
            queryCache[query] = count;
            console.log(`[${count}] ${name}`);
          }

          if (count) {
            // we have affected CI's for this version. Add to managed product.
            vendorProductVersionIds.push(vendorProductVersionId);
          }
        }
      }
      console.log("---------------------------");
      console.log("Totals");
      console.log("---------------------------");
      console.log(`Versions with CI's: ${vendorProductVersionIds.length}`);
      console.log(`Queries saved with Caching : ${cacheCount}`);

      const productParams = {
        TableName: PRODUCTS_TABLE,
        // Item: item,
        Key: {
          clientId: managedProduct.clientId,
          name: managedProduct.name,
        },
        UpdateExpression:
          "set vendorProductVersionIds=:vendorProductVersionIds",
        ExpressionAttributeValues: {
          ":vendorProductVersionIds": vendorProductVersionIds,
        },
        ReturnValues: "UPDATED_NEW",
      };
      const result = await db.updateItem(productParams);
      console.log("result", result);
    } // managedProduct loop
  } catch (e) {
    // error

    console.log("e", e);
    return e;
  }
};

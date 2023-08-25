import { create } from "apisauce";
import vendors from "../constants/vendors";

// import { store } from 'App/Stores/CreateStore'
/**
 * This is an example of a service that connects to a 3rd party API.
 *
 * Feel free to remove this example from your application.
 */

let baseURL = "/";
const apiClient = create({
  /**
   * Import the config from the App/Config/index.js file
   */
  baseURL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  timeout: 20000,
});
const authMonitor = (response) => {
  if (response.status === 401) {
    // handle auth issue
    console.log("auth issue with sn");
  }
};
apiClient.addMonitor(authMonitor);
console.log("init apiClient", apiClient);

function connectionTest(authToken) {
  return apiClient
    .get(`api/now/table/cmdb_model?sysparm_fields=sys_id`, null, {
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Basic ${authToken}`,
      },
    })
    .then((response) => {
      console.log("responsex", response);
      return response;
    })
    .catch((e) => console.log("e", e));
}

function getProductModels(vendorId) {
  console.log("getProductModels");

  return apiClient
    .get(
      `api/now/table/cmdb_model?sysparm_query=${vendors[vendorId].cmdb.products.sysparm_query}&sysparm_fields=${vendors[vendorId].cmdb.products.sysparm_fields}`
    )
    .then((response) => {
      if (response.ok) {
        const { data } = response;
        return data.result;
      }

      return null;
    });
}

function queryTableAPI(query) {
  console.log("getProductModels");

  return apiClient.get(`api/now/table/${query}`).then((response) => {
    if (response.ok) {
      const { data } = response;
      return data.result;
    }

    return null;
  });
}
function getProductsWithSerialNumbers(model, vendorId) {
  console.log("getProductModels");

  return apiClient
    .get(
      `api/now/table/${vendors[vendorId].cmdb.ciWithSerialNumber.table}?sysparm_query=model_id.sys_id=${model}^${vendors[vendorId].cmdb.ciWithSerialNumber.sysparm_query}&sysparm_fields=${vendors[vendorId].cmdb.ciWithSerialNumber.sysparm_fields}`
    )
    .then((response) => {
      if (response.ok) {
        const { data } = response;
        return data.result;
      }

      return null;
    });
}

function getCiComputers(vendorId) {
  return apiClient
    .get(
      `api/now/table/cmdb_ci_computer?sysparm_query=${vendors[vendorId].cmdb.products.sysparm_query}&sysparm_fields=${vendors[vendorId].cmdb.products.sysparm_fields}`
    )
    .then((response) => {
      if (response.ok) {
        const { data } = response;
        return data.result;
      }

      return null;
    });
}

// eslint-disable-next-line
export default {
  apiClient,
  getProductModels,
  getProductsWithSerialNumbers,
  connectionTest,
  getCiComputers,
  queryTableAPI,
};

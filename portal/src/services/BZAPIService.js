import { create } from 'apisauce';
import { aws } from '../config';

let bzAuthToken = null;
try {
  bzAuthToken = localStorage.getItem('bzAuthToken');
} catch (e) {
  console.log('No token found for BZAPI in localstorage');
}

const apiClient = create({
  baseURL: aws.apiGateway.URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Authorization: bzAuthToken ? `Bearer ${bzAuthToken}` : ''
  },
  timeout: 20000
});

const authMonitor = response => {
  if (response.status === 401 || response.status === 403) {
    console.log('Receieved a unauthorized. Remove token and redirecting..');
    localStorage.removeItem('bzAuthToken');
    localStorage.setItem('redirect', window.location.pathname);
    window.location.href = aws.cognito.loginUrl;
  }
};
// Montior API for 401s
apiClient.addMonitor(authMonitor);

async function listManagedProducts(vendorId) {
  const response = await apiClient.get(`/managedProducts?vendorId=${vendorId}`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getManagedProduct(productId) {
  const response = await apiClient.get(`/managedProducts/${productId}`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getDashboard() {
  const response = await apiClient.get(`/dashboard`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getVendorProducts(vendorId) {
  const response = await apiClient.get(`/vendors/${vendorId}/products`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getVendor(vendorId) {
  const response = await apiClient.get(`/vendors/${vendorId}`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function vendorTestCreds(vendorId, data) {
  const response = await apiClient.post(`/vendors/testCredentials/${vendorId}`, data);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getVendors() {
  const response = await apiClient.get(`/vendors`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getCiscoProductIdBySerialNumber(serialNumber) {
  const response = await apiClient.get(`/vendors/cisco/productIdBySn/${serialNumber}`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function createOrUpdateManagedProduct(body) {
  const response = await apiClient.post('/managedProducts', body);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function deleteManagedProduct(productId) {
  const response = await apiClient.delete(`/managedProducts/${productId}`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function getSetting(settingId) {
  const response = await apiClient.get(`/setting/${settingId}`);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function createOrUpdateAWSSecret(body) {
  const response = await apiClient.put('/setting/secret', body);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function saveSetting(settingId, body) {
  const response = await apiClient.post(`/setting/${settingId}`, body);
  if (response.status === 200 || response.status === 201) return response.data ? response.data : null;
  throw new Error('Request Failed');
}
async function createSupportTicket(body) {
  const response = await apiClient.post(`/support/ticket`, body);
  if (response.status === 200 || response.status === 201) return response;
  throw new Error('Request Failed');
}

export default {
  apiClient,
  createSupportTicket,
  listManagedProducts,
  getManagedProduct,
  getDashboard,
  getVendorProducts,
  getVendor,
  getVendors,
  createOrUpdateManagedProduct,
  deleteManagedProduct,
  getSetting,
  saveSetting,
  vendorTestCreds,
  getCiscoProductIdBySerialNumber,
  createOrUpdateAWSSecret
};

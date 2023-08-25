import { vendorSchemas } from './vendorSchemas';

export function validateVendor(vendorId, data) {
  const { error } = vendorSchemas[vendorId].validate(data);
  return !error;
}

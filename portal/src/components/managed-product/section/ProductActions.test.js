import React from 'react';
import { shallow } from 'enzyme';
import ProductActions from './ProductActions';
test('should test ProductActions component', () => {
  const wrapper = shallow(
    <ProductActions
      vendorId="cisco"
      snProductOptions={[]}
      isLoading={false}
      handleDelete={() => {}}
      handleSave={() => {}}
      handleSaveAndAdd={() => {}}
      productId={'1'}
    />
  );
  expect(wrapper).toMatchSnapshot();
});

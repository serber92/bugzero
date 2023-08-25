import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormNetApp from './ConfigFormNetApp';
test('should test ConfigFormNetApp component', () => {
  const wrapper = shallow(<ConfigFormNetApp vendorId="netapp" vendorLabel="NetApp" />);
  expect(wrapper).toMatchSnapshot();
});

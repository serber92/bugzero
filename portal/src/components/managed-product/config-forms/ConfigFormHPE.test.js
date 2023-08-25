import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormHPE from './ConfigFormHPE';
test('should test ConfigFormHPE component', () => {
  const wrapper = shallow(<ConfigFormHPE vendorId="hpe" vendorLabel="HPE" />);
  expect(wrapper).toMatchSnapshot();
});

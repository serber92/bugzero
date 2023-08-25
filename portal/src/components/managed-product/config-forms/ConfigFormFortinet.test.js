import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormFortinet from './ConfigFormFortinet';
test('should test ConfigFormFortinet component', () => {
  const wrapper = shallow(<ConfigFormFortinet vendorId="fortinet" vendorLabel="Fortinet" />);
  expect(wrapper).toMatchSnapshot();
});

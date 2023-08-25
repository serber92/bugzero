import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormRedHat from './ConfigFormRedHat';
test('should test ConfigFormRedHat component', () => {
  const wrapper = shallow(<ConfigFormRedHat vendorId="rh" vendorLabel="Red Hat" />);
  expect(wrapper).toMatchSnapshot();
});

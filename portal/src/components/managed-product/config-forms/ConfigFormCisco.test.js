import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormCisco from './ConfigFormCisco';
test('should test ConfigFormCisco component', () => {
  const wrapper = shallow(<ConfigFormCisco vendorId="cisco" vendorLabel="Cisco" />);
  expect(wrapper).toMatchSnapshot();
});

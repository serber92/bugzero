import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormCisco from '../components/managed-product/config-forms/ConfigFormCisco';
test('should test EditForm component', () => {
  const wrapper = shallow(<ConfigFormCisco vendorId="cisco" vendorLabel="Cisco" />);
  expect(wrapper).toMatchSnapshot();
});

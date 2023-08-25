import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormVeeam from './ConfigFormVeeam';
test('should test ConfigFormVeeam component', () => {
  const wrapper = shallow(<ConfigFormVeeam vendorId="veeam" vendorLabel="Veeam" />);
  expect(wrapper).toMatchSnapshot();
});

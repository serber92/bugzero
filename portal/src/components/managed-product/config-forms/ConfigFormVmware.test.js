import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormVmware from './ConfigFormVmware';
test('should test ConfigFormVmware component', () => {
  const wrapper = shallow(<ConfigFormVmware vendorId="vmware" vendorLabel="VMware" />);
  expect(wrapper).toMatchSnapshot();
});

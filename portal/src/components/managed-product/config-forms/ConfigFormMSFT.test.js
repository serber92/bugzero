import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormMSFT from './ConfigFormMSFT';
test('should test ConfigFormMSFT component', () => {
  const wrapper = shallow(<ConfigFormMSFT vendorId="msft" vendorLabel="Microsoft" />);
  expect(wrapper).toMatchSnapshot();
});

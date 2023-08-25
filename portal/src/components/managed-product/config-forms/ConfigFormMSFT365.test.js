import React from 'react';
import { shallow } from 'enzyme';
import ConfigFormMSFT365 from './ConfigFormMSFT365';
test('should test ConfigFormMSFT365 component', () => {
  const wrapper = shallow(<ConfigFormMSFT365 vendorId="msft365" vendorLabel="Microsoft 365" />);
  expect(wrapper).toMatchSnapshot();
});

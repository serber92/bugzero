import React from 'react';
import { shallow } from 'enzyme';
import EditForm from './EditForm';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: () => ({
    vendorId: 'cisco',
    managedProductId: 1
  })
}));

test('should test EditForm component', () => {
  const wrapper = shallow(<EditForm vendorId="cisco" vendorLabel="Cisco" />);
  expect(wrapper).toMatchSnapshot();
});

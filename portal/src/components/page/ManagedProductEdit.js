import React from 'react';
import PropTypes from 'prop-types';
import VENDORS from '../../constants/vendors';
import { useParams } from 'react-router-dom';
// config forms
import EditForm from '../managed-product/EditForm';
// import EditFormHPE from '../managed-product/config-forms/EditFormHPE';
// import EditFormCisco from '../managed-product/config-forms/EditFormCisco';
// import EditFormVmware from '../managed-product/config-forms/EditFormVmware';
// import EditFormMSFT from '../managed-product/config-forms/EditFormMSFT';
import Heading from '../common/Heading';

export default function ManagedProductEdit() {
  const { vendorId } = useParams();
  return (
    <>
      <Heading
        title={`${VENDORS[vendorId].name} Managed Product`}
        subtitle={`Specify configuration details`}
        className="mb-4 mt-3"
        icon="edit"
      />
      <EditForm vendorLabel={VENDORS[vendorId].name} vendorId={vendorId} />
      {/* {React.createElement(managedProductForms[vendorId], { vendorLabel: VENDORS[vendorId].name, vendorId })} */}
    </>
  );
}

ManagedProductEdit.propTypes = {
  forms: PropTypes.func,
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};

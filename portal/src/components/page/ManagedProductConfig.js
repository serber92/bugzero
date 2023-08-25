import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router-dom';
// config forms
import ConfigFormRedHat from '../managed-product/config-forms/ConfigFormRedHat';
import ConfigFormHPE from '../managed-product/config-forms/ConfigFormHPE';
import ConfigFormFortinet from '../managed-product/config-forms/ConfigFormFortinet';
import ConfigFormCisco from '../managed-product/config-forms/ConfigFormCisco';
import ConfigFormMSFT365 from '../managed-product/config-forms/ConfigFormMSFT365';
import ConfigFormMongoDB from '../managed-product/config-forms/ConfigFormMongoDB';
import ConfigFormVmware from '../managed-product/config-forms/ConfigFormVmware';
import ConfigFormVeeam from '../managed-product/config-forms/ConfigFormVeeam';
import ConfigFormNetApp from '../managed-product/config-forms/ConfigFormNetApp';
import ConfigFormMSFT from '../managed-product/config-forms/ConfigFormMSFT';
import ConfigFormAWS from '../managed-product/config-forms/ConfigFormAWS';
import Heading from '../common/Heading';
import BZAPIService from '../../services/BZAPIService';
import Loader from '../common/Loader';

const managedProductForms = {
  aws: ConfigFormAWS,
  rh: ConfigFormRedHat,
  hpe: ConfigFormHPE,
  msft: ConfigFormMSFT,
  msft365: ConfigFormMSFT365,
  cisco: ConfigFormCisco,
  mongodb: ConfigFormMongoDB,
  vmware: ConfigFormVmware,
  veeam: ConfigFormVeeam,
  netapp: ConfigFormNetApp,
  fortinet: ConfigFormFortinet
};

export default function ManagedProductConfig() {
  const { vendorId } = useParams();
  const [isLoading, setIsLoading] = useState(true);
  const [vendor, setVendor] = useState(null);
  console.log('forms', managedProductForms);
  console.log('form', managedProductForms[vendorId]);

  useEffect(() => {
    async function onLoad() {
      try {
        const vendor = await BZAPIService.getVendor(vendorId);
        setVendor(vendor);
        setIsLoading(false);
      } catch (e) {
        console.log('e', e);
      }
    }

    onLoad();
  }, [vendorId]);
  if (isLoading) return <Loader />;

  return (
    <>
      <Heading
        title={`${vendor.name} Configuration`}
        subtitle={`Specify configuration details`}
        className="mb-4 mt-3"
        icon="cog"
      />

      {React.createElement(managedProductForms[vendorId], {
        vendorLabel: vendor.name,
        vendorId,
        vendorPriorityOptions: vendor.vendorData.priorities || [],
        vendorStatusOptions: vendor.vendorData.statuses || [],
        vendorBugCategories: vendor.vendorData.categories || [],
        vendorBugTypes: vendor.vendorData.types || [],
        vendorResolutionOptions: vendor.vendorData.resolutions || [],
        vendorEventScopeOptions: vendor.vendorData.eventScopes || []
      })}
    </>
  );
}

ManagedProductConfig.propTypes = {
  forms: PropTypes.func,
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};

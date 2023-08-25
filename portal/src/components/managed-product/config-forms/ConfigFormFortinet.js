import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useHistory } from 'react-router-dom';

import LoaderButton from '../../loader-button/LoaderButton';
import { onError } from '../../../libs/errorLib';
import { useFormFields } from '../../../libs/hooksLib';
import PropTypes from 'prop-types';
import { Card, CardBody, CardTitle, CardText, Col, Row, Button } from 'reactstrap';
import Loader from '../../common/Loader';
import FalconCardHeader from '../../common/FalconCardHeader';
import BZAPIService from '../../../services/BZAPIService';
import CMDBCompany from '../ServiceNow/CMDBCompany';
import ProductPriority from '../section/ProductPriority';
import CMDBAffectedCIQuery from '../ServiceNow/CMDBAffectedCIQuery';

// constants
import SETTINGS from '../../../constants/settings';
import VENDORS from '../../../constants/vendors';
import SERVICENOW from '../../../constants/servicenow';

const ConfigFormFortinet = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();
  const [fields, handleFieldChange] = useFormFields({
    snCompanySysId: '',
    snAffectedCIQuery: ''
  });
  const [priorityMaps, setPriorityMaps] = useState([]);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [vendorStatuses, setVendorStatuses] = useState([]);

  const vendor = VENDORS[vendorId];
  const snPriorityOptions = SERVICENOW.SN_PRIORITY_OPTIONS;

  const vendorPriorityOptions = vendor.priorities;

  useEffect(() => {
    async function onLoad() {
      console.log('onload');
      try {
        let settings = (await BZAPIService.getSetting(vendorId)) || {};
        // Init defaults
        if (!settings)
          settings = {
            snCompanySysId: '',
            vendorPriorities: [],
            snAffectedCIQuery: ''
          };
        // Set priority maps
        if (!settings.vendorPriorities) settings.vendorPriorities = [];
        if (!settings.vendorStatuses) settings.vendorStatuses = [];

        console.log('settings.vendorStatuses', settings.vendorStatuses);
        setVendorStatuses(settings.vendorStatuses);
        const priorityMaps = settings.vendorPriorities.map(priority => {
          const result = {
            vendorPriority: vendorPriorityOptions.find(e => e.value === priority.vendorPriority),
            snPriority: snPriorityOptions.find(e => e.value === priority.snPriority)
          };

          return result;
        });
        console.log('vendor.statuses', vendor.statuses);
        setVendorStatusOptions(vendor.statuses);
        console.log('priorityMaps', priorityMaps);
        setPriorityMaps(priorityMaps);
        fields.snCompanySysId = settings.snCompanySysId || '';
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';

        setIsLoading(false);
      } catch (e) {
        onError(e);
      }
    }

    onLoad();
  }, []);
  async function saveConfig() {
    console.log('saveConfig', fields);
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });
    const data = {
      snCompanySysId: fields.snCompanySysId,
      vendorPriorities,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      vendorStatuses,
      type: SETTINGS.VENDOR
    };

    return BZAPIService.saveSetting(vendorId, data);
  }

  async function handleSave() {
    try {
      setIsLoading(true);
      setIsSubmitted(true);
      // Validate
      if (!fields.snCompanySysId) {
        console.log('error');
        setIsLoading(false);
        return;
      }
      // validate priority maps
      let validPriorities = true;
      priorityMaps.map(item => {
        if (!item.vendorPriority || !item.snPriority) validPriorities = false;
        return item;
      });
      if (!validPriorities) {
        console.log('Invalid priorities');
        setIsLoading(false);
        return false;
      }
      await saveConfig();
      setIsLoading(false);
      setIsSubmitted(false);
      toast.success(`Settings Saved!`);
    } catch (e) {
      setIsLoading(false);
      toast.error('Failed to save.');
      console.log('e', e);
    }
  }
  function handleSelectChange(e, setHook) {
    // if e is null set to empty array for multi-select
    console.log(e, setHook);

    const selected = e || [];
    if (Array.isArray(selected)) setHook(selected.map(el => el.value));
    else setHook(selected.value);
  }

  if (isLoading && !isSubmitted) return <Loader />;

  return (
    <form noValidate style={{ minWidth: '100%' }}>
      <Card bg={'light'} text={'dak'} className="mb-4">
        <FalconCardHeader title="Vendor Settings" />

        <CardBody>
          <CardTitle>Manage your {vendorLabel} settings</CardTitle>
          <CardText>Configure your preferences for {vendorLabel}</CardText>
          <Row>
            <Col lg="6">
              <CMDBCompany
                snCompanySysId={fields.snCompanySysId}
                handleFieldChange={handleFieldChange}
                isSubmitted={isSubmitted}
              />
            </Col>
          </Row>
          <CMDBAffectedCIQuery
            snAffectedCIQuery={fields.snAffectedCIQuery}
            handleFieldChange={handleFieldChange}
            isSubmitted={isSubmitted}
          />
        </CardBody>
      </Card>
      <ProductPriority
        title="Default Bug Configuration"
        vendorPriorityOptions={vendorPriorityOptions}
        vendorStatusOptions={vendorStatusOptions}
        handleSelectChange={handleSelectChange}
        setVendorStatuses={setVendorStatuses}
        vendorStatuses={vendorStatuses}
        isSubmitted={isSubmitted}
        priorityMaps={priorityMaps}
        setPriorityMaps={setPriorityMaps}
        snPriorityOptions={snPriorityOptions}
      />
      <Row className="flex-between-center">
        <Col xs="auto">
          <Button
            block
            color="falcon-danger"
            onClick={() => {
              console.log(`/vendors/${vendorId}/configuration`);
              history.goBack();
            }}
          >
            Cancel
          </Button>
        </Col>
        <Col xs="auto">
          <LoaderButton block color="falcon-primary" onClick={handleSave} name="save-and-add" isLoading={isLoading}>
            Save changes
          </LoaderButton>
        </Col>
      </Row>
    </form>
  );
};
ConfigFormFortinet.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormFortinet;

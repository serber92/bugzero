import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { FieldGroup } from '../../../libs/formLib';
import ButtonIcon from '../../common/ButtonIcon';
import { useHistory } from 'react-router-dom';

import LoaderButton from '../../loader-button/LoaderButton';
import { onError } from '../../../libs/errorLib';
import { useFormFields } from '../../../libs/hooksLib';
import PropTypes from 'prop-types';
import { Row, Card, CardBody, FormGroup, Label, FormFeedback, Col, Button } from 'reactstrap';
import Loader from '../../common/Loader';
import FalconCardHeader from '../../common/FalconCardHeader';
import BZAPIService from '../../../services/BZAPIService';
import CMDBCompany from '../ServiceNow/CMDBCompany';
import VendorDaysBack from '../Vendor/VendorsDaysBack';
import ProductPriority from '../section/ProductPriority';
import CMDBAffectedCIQuery from '../ServiceNow/CMDBAffectedCIQuery';

// constants
import SETTINGS from '../../../constants/settings';
import VENDORS from '../../../constants/vendors';
import SERVICENOW from '../../../constants/servicenow';

const ConfigFormMongoDB = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();

  //  const [config, setConfig] = useState(null);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [vendorStatuses, setVendorStatuses] = useState([]);
  const [vendorResolutionOptions, setVendorResolutionOptions] = useState([]);
  const [vendorResolutions, setVendorResolutions] = useState([]);

  const [priorityMaps, setPriorityMaps] = useState([]);

  const vendor = VENDORS[vendorId];
  const snPriorityOptions = SERVICENOW.SN_PRIORITY_OPTIONS;

  const vendorPriorityOptions = vendor.priorities;

  const [fields, handleFieldChange] = useFormFields({
    daysBack: '60',
    snCompanySysId: '',
    snAffectedCIQuery: ''
  });

  useEffect(() => {
    async function onLoad() {
      console.log('load...');

      try {
        let settings = (await BZAPIService.getSetting(vendorId)) || {};
        // Init defaults
        if (!settings)
          settings = {
            daysBack: 60,
            vendorPriorities: [],
            vendorStatuses: [],
            vendorResolutions: [],
            snAffectedCIQuery: ''
          };

        //setConfig(settings);
        fields.daysBack = settings.daysBack;
        fields.snCompanySysId = settings.snCompanySysId;
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';

        // Set priority maps
        if (!settings.vendorPriorities) settings.vendorPriorities = [];
        if (!settings.vendorStatuses) settings.vendorStatuses = [];
        if (!settings.vendorResolutions) settings.vendorResolutions = [];
        setVendorResolutions(settings.vendorResolutions);

        setVendorStatuses(settings.vendorStatuses);

        const priorityMaps = settings.vendorPriorities.map(priority => {
          const result = {
            vendorPriority: vendorPriorityOptions.find(e => e.value === priority.vendorPriority),
            snPriority: snPriorityOptions.find(e => e.value === priority.snPriority)
          };

          return result;
        });
        setVendorStatusOptions(vendor.statuses);
        setVendorResolutionOptions(vendor.resolutions);
        console.log('priorityMaps', priorityMaps);
        setPriorityMaps(priorityMaps);
        setIsLoading(false);
      } catch (e) {
        onError(e);
      }
    }

    onLoad();
  }, []);

  async function saveConfig() {
    // save client config
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });

    const data = {
      daysBack: fields.daysBack,
      snCompanySysId: fields.snCompanySysId,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      vendorPriorities,
      vendorStatuses,
      vendorResolutions,
      type: SETTINGS.VENDOR
    };

    return BZAPIService.saveSetting(vendorId, data);
  }

  async function handleSave() {
    try {
      setIsSubmitted(true);
      setIsLoading(true);
      // Validate
      if (!fields.daysBack || !fields.snCompanySysId) {
        console.log(fields);
        console.log('failed validation');

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
      // set updated secretId
      setIsLoading(false);
      setIsSubmitted(false);
      toast.success(`Settings Saved!`);
    } catch (e) {
      setIsLoading(false);
      toast.error('Failed to save.');
      console.log('e', e);
    }
  }

  // Generic function to handle react-select single/multi-selects
  function handleSelectChange(e, setHook) {
    // if e is null set to empty array for multi-select
    console.log(e, setHook);

    const selected = e || [];
    if (Array.isArray(selected)) setHook(selected.map(el => el.value));
    else setHook(selected.value);
  }
  if (isLoading && !isSubmitted) return <Loader />;

  return (
    <>
      <form noValidate style={{ minWidth: '100%' }}>
        <Card bg={'light'} text={'dak'} className="mb-4">
          <FalconCardHeader title="Vendor settings" />
          <CardBody>
            <Row>
              <Col lg="6">
                <VendorDaysBack
                  daysBack={fields.daysBack}
                  handleFieldChange={handleFieldChange}
                  isSubmitted={isSubmitted}
                />
              </Col>
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
          vendorResolutionOptions={vendorResolutionOptions}
          handleSelectChange={handleSelectChange}
          setVendorStatuses={setVendorStatuses}
          vendorStatuses={vendorStatuses}
          isSubmitted={isSubmitted}
          priorityMaps={priorityMaps}
          setVendorResolutions={setVendorResolutions}
          vendorResolutions={vendorResolutions}
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
    </>
  );
};
ConfigFormMongoDB.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormMongoDB;

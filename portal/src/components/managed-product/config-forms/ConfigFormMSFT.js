import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useHistory } from 'react-router-dom';

import LoaderButton from '../../loader-button/LoaderButton';
import { onError } from '../../../libs/errorLib';
import { useFormFields } from '../../../libs/hooksLib';
import PropTypes from 'prop-types';
import ProductPriority from '../section/ProductPriority';

import { Card, CardBody, Col, Row, Button, FormFeedback, Label, FormGroup } from 'reactstrap';
import Loader from '../../common/Loader';
import FalconCardHeader from '../../common/FalconCardHeader';
import BZAPIService from '../../../services/BZAPIService';
import CMDBAffectedCIQuery from '../ServiceNow/CMDBAffectedCIQuery';
import CMDBCompany from '../ServiceNow/CMDBCompany';
import VendorDaysBack from '../Vendor/VendorsDaysBack';
// constants
import SETTINGS from '../../../constants/settings';
import VENDORS from '../../../constants/vendors';
import SERVICENOW from '../../../constants/servicenow';
import ButtonIcon from '../../common/ButtonIcon';
import { FieldGroup } from '../../../libs/formLib';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

const ConfigFormMSFT = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isValidCredentials, setIsValidCredentials] = useState(false);

  const [isTestingValidCredentials, setIsTestingValidCredentials] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [vendorStatuses, setVendorStatuses] = useState([]);

  const history = useHistory();
  const [fields, handleFieldChange] = useFormFields({
    secretId: '',
    daysBack: '',
    username: '',
    password: '',
    snCompanySysId: '',
    snAffectedCIQuery: ''
  });
  const [priorityMaps, setPriorityMaps] = useState([]);

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
            secretId: '',
            daysBack: '60',
            snCompanySysId: '',
            vendorStatuses: [],
            snAffectedCIQuery: ''
          };
        if (!settings.vendorPriorities) settings.vendorPriorities = [];
        if (!settings.vendorStatuses) settings.vendorStatuses = [];
        setVendorStatuses(settings.vendorStatuses);
        setVendorStatusOptions(vendor.statuses);

        //setConfig(settings);
        fields.daysBack = settings.daysBack | '';
        fields.snCompanySysId = settings.snCompanySysId || '';
        fields.secretId = settings.secretId;
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';
        console.log('settings', settings);
        const priorityMaps = settings.vendorPriorities.map(priority => {
          const result = {
            vendorPriority: vendorPriorityOptions.find(e => e.value === priority.vendorPriority),
            snPriority: snPriorityOptions.find(e => e.value === priority.snPriority)
          };

          return result;
        });
        setPriorityMaps(priorityMaps);

        setIsLoading(false);
      } catch (e) {
        onError(e);
      }
    }

    onLoad();
  }, [fields.secretId]);
  async function saveServiceAWSSecret() {
    const data = {
      secret: {
        username: fields.username,
        password: fields.password
      },
      vendorId: 'msft',
      key: 'admin'
    };
    // service api secret
    console.log('fields.secretId', fields.secretId);
    return BZAPIService.createOrUpdateAWSSecret(data);
  }

  async function testCreds() {
    setIsTestingValidCredentials(true);
    const data = {
      username: fields.username,
      password: fields.password
    };
    const result = await BZAPIService.vendorTestCreds(vendorId, data);
    setIsTestingValidCredentials(false);
    if (result && result.completed) {
      // valid creds
      setIsValidCredentials(true);
      setIsAddingCredentials(false);
      toast.success(`Credentials validated!`);
    } else {
      toast.error('Error Validating credentials.');
    }

    console.log('result', result);
  }

  async function saveConfig(serviceSecret) {
    console.log('saveConfig', fields);
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });

    const data = {
      secretId: serviceSecret.Name,
      daysBack: fields.daysBack,
      snCompanySysId: fields.snCompanySysId,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      vendorPriorities,
      vendorStatuses,
      type: SETTINGS.VENDOR
    };

    return BZAPIService.saveSetting(vendorId, data);
  }

  async function handleSave() {
    try {
      setIsLoading(true);
      setIsSubmitted(true);

      // Validate Secrets

      if (!fields.secretId) {
        if (!fields.username || !fields.password) {
          console.log('missing secret');
          setIsLoading(false);
          return;
        }
      }

      // Validate
      if (!fields.daysBack || !fields.snCompanySysId) {
        console.log('error');
        setIsLoading(false);
        return;
      }
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

      let serviceSecret;

      if (fields.password && fields.username) {
        // Updated secrets
        serviceSecret = await saveServiceAWSSecret();
      } else {
        // use existing secrets
        serviceSecret = { Name: fields.secretId };
      }
      console.log('serviceSecret', serviceSecret);
      if (!serviceSecret || !serviceSecret.Name) {
        setIsLoading(false);
        throw Error('Missing Secret');
      }
      await saveConfig(serviceSecret);
      fields.secretId = serviceSecret.Name;

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
    <form noValidate style={{ minWidth: '100%' }}>
      <Card bg={'light'} text={'dak'} className="mb-4">
        <FalconCardHeader title="Vendor settings" />
        <CardBody>
          <Row form>
            <Col lg="12">
              <FormGroup>
                <Label>
                  Microsoft 365 Admin Credentials
                  <span style={{ color: '#bd472a' }}>*</span>
                </Label>
                {!isAddingCredentials ? (
                  <>
                    <div>
                      <ButtonIcon
                        onClick={() => setIsAddingCredentials(true)}
                        color="falcon-default"
                        size="sm"
                        icon="plus"
                        iconClassName="fs--2"
                      >
                        Set Credentials
                      </ButtonIcon>
                      {/* <Button variant="outline-primary" onClick={() => setIsAddingCredentials(true)}>
                          <FontAwesomeIcon icon={'plus'} /> Set Credentials
                        </Button> */}

                      {fields.secretId || isValidCredentials ? (
                        <>
                          {'  '}
                          <FontAwesomeIcon icon={'check'} style={{ color: 'green', marginLeft: '10px' }} /> Microsoft
                          Credentials Stored
                        </>
                      ) : null}
                    </div>
                  </>
                ) : (
                  <>
                    <Row>
                      <Col lg="6">
                        <FieldGroup
                          type="text"
                          id="username"
                          onChange={handleFieldChange}
                          value={fields.username}
                          label={'Microsoft 365 Admin Username'}
                          showFeedback={!isValidCredentials}
                          feedback={'Username has not been validated or is invalid.'}
                          placeholder="Enter Microsoft 365 Admin Username"
                          style={{ marginBottom: '10px' }}
                          required
                        />
                      </Col>
                      <Col lg="6">
                        <FieldGroup
                          type="password"
                          id="password"
                          autoComplete="new-password"
                          onChange={handleFieldChange}
                          value={fields.password}
                          label={'Microsoft 365 Admin Password'}
                          showFeedback={!isValidCredentials}
                          feedback={'Password has not been validated or is invalid.'}
                          placeholder="Enter Microsoft 365 Admin Password"
                          style={{ marginBottom: '10px' }}
                          required
                        />
                      </Col>
                    </Row>
                    <LoaderButton
                      isLoading={isTestingValidCredentials}
                      onClick={testCreds}
                      color="falcon-default"
                      size="sm"
                      icon="check"
                      iconClassName="fs--2"
                      style={{ marginRight: '10px' }}
                    >
                      Test and update
                    </LoaderButton>{' '}
                    <ButtonIcon
                      onClick={() => setIsAddingCredentials(false)}
                      color="falcon-default"
                      size="sm"
                      icon="times"
                      iconClassName="fs--2"
                      style={{ marginRight: '10px' }}
                    >
                      Cancel
                    </ButtonIcon>
                  </>
                )}
                <FormFeedback
                  className={!fields.secretId && !fields.refreshToken && isSubmitted ? 'd-block' : ''}
                  type="invalid"
                >
                  Please specify credentials.
                </FormFeedback>
              </FormGroup>
            </Col>
          </Row>
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
        setVendorStatuses={setVendorStatuses}
        vendorStatuses={vendorStatuses}
        handleSelectChange={handleSelectChange}
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
ConfigFormMSFT.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormMSFT;

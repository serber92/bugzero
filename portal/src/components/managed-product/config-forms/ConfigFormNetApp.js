import React, {useEffect, useState} from 'react';
import {toast} from 'react-toastify';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {FieldGroup} from '../../../libs/formLib';
import ButtonIcon from '../../common/ButtonIcon';
import {useHistory} from 'react-router-dom';

import LoaderButton from '../../loader-button/LoaderButton';
import {onError} from '../../../libs/errorLib';
import {useFormFields} from '../../../libs/hooksLib';
import PropTypes from 'prop-types';
import {Button, Card, CardBody, Col, FormFeedback, FormGroup, Label, ListGroup, ListGroupItem, Row} from 'reactstrap';
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

const ConfigFormNetApp = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();

  //  const [config, setConfig] = useState(null);
  const [isValidCredentials, setIsValidCredentials] = useState(false);
  const [isTestingValidCredentials, setIsTestingValidCredentials] = useState(false);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [vendorStatuses, setVendorStatuses] = useState([]);
  const [customers, setCustomers] = useState([]);

  const [priorityMaps, setPriorityMaps] = useState([]);

  const vendor = VENDORS[vendorId];
  const snPriorityOptions = SERVICENOW.SN_PRIORITY_OPTIONS;

  const vendorPriorityOptions = vendor.priorities;

  const [fields, handleFieldChange] = useFormFields({
    secretId: '',
    refreshToken: '',
    snCompanySysId: '',
    snAffectedCIQuery: ''
  });

  useEffect(() => {
    async function onLoad() {
      console.log('load...');

      try {
        let settings = (await BZAPIService.getSetting(vendorId)) || {};
        // Init defaults
        console.log('settings', settings);
        if (!settings)
          settings = {
            secretId: '',
            snCompanySysId: '',
            vendorPriorities: [],
            vendorStatuses: [],
            snAffectedCIQuery: ''
          };

        //setConfig(settings);
        fields.snCompanySysId = settings.snCompanySysId || '';
        fields.secretId = settings.secretId;
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';

        if (settings.activeIqCustomers) setCustomers(settings.activeIqCustomers);

        // Set priority maps
        if (!settings.vendorPriorities) settings.vendorPriorities = [];
        if (!settings.vendorStatuses) settings.vendorStatuses = [];
        setVendorStatuses(settings.vendorStatuses);

        const priorityMaps = settings.vendorPriorities.map(priority => {
          const result = {
            vendorPriority: vendorPriorityOptions.find(e => e.value === priority.vendorPriority),
            snPriority: snPriorityOptions.find(e => e.value === priority.snPriority)
          };

          return result;
        });
        setVendorStatusOptions(vendor.statuses);
        console.log('priorityMaps', priorityMaps);
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
        refreshToken: fields.refreshToken
      },
      vendorId: 'netapp',
      key: 'activeiq'
    };
    // service api secret
    console.log('fields.secretId', fields.secretId);
    return BZAPIService.createOrUpdateAWSSecret(data);
  }
  function cancelCreds() {
    fields.refreshToken = '';
    setIsAddingCredentials(false);
  }

  async function testCreds() {
    setIsTestingValidCredentials(true);
    const data = {
      refreshToken: fields.refreshToken
    };
    const result = await BZAPIService.vendorTestCreds(vendorId, data);
    setIsTestingValidCredentials(false);
    if (result && result.completed) {
      // valid creds
      console.log('result.active_iq_customers', result.active_iq_customers);
      fields.refreshToken = result.refresh_token;
      setIsValidCredentials(true);
      setCustomers([...result.active_iq_customers]);
      setIsAddingCredentials(false);
      toast.success(`Refresh token validated.`);
    } else {
      toast.error(`Unable to validate refresh token.`);
    }

    console.log('result', result);
  }

  async function saveConfig(serviceSecret) {
    // save client config
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });

    const data = {
      secretId: serviceSecret.Name,
      snCompanySysId: fields.snCompanySysId,
      activeIqCustomers: customers,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      vendorPriorities,
      vendorStatuses,
      type: SETTINGS.VENDOR
    };

    return BZAPIService.saveSetting(vendorId, data);
  }

  async function handleSave() {
    try {
      setIsSubmitted(true);
      setIsLoading(true);
      // Validate
      if (!fields.snCompanySysId) {
        console.log(fields);
        console.log('failed validation');

        setIsLoading(false);
        return;
      }

      // Validate Secrets
      if (!fields.secretId) {
        if (!fields.refreshToken) {
          console.log('Missing secret');
          setIsLoading(false);
          return;
        }
      }

      let serviceSecret;

      if (fields.refreshToken) {
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

      await saveConfig(serviceSecret);
      // set updated secretId
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
  function handleToggleCustomer(index, disabled) {
    customers[index].disabled = disabled;

    setCustomers([...customers]);
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
        <input type="hidden" value="prayer" />
        <Card bg={'light'} text={'dak'} className="mb-4">
          <FalconCardHeader title="Vendor settings" />
          <CardBody>
            <Row form>
              <Col lg="12">
                <FormGroup>
                  <Label>
                    NetApp API Credentials
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

                        {customers.length ? (
                          <>
                            {'  '}
                            <FontAwesomeIcon icon={'check'} style={{ color: 'green', marginLeft: '10px' }} /> NetApp
                            Credentials Stored
                            <Row form>
                              <Col lg="12">
                                <FormGroup>
                                  <Label>
                                    NetApp ActiveIQ Customers
                                    <span style={{ color: '#bd472a' }}>*</span>
                                  </Label>
                                  <ListGroup style={{ maxHeight: '500px', overflowY: 'scroll' }}>
                                    {customers.map(({ customerId, customerName, disabled }, index) => {
                                      console.log(`${customerName} ${disabled}`);

                                      return (
                                        <ListGroupItem key={customerId}>
                                          <input
                                            type="checkbox"
                                            checked={!disabled}
                                            onChange={() => handleToggleCustomer(index, disabled ? 0 : 1)}
                                          />{' '}
                                          {customerName}
                                        </ListGroupItem>
                                      );
                                    })}
                                  </ListGroup>
                                </FormGroup>
                              </Col>
                            </Row>
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
                            id="refreshToken"
                            autoComplete="new-password"
                            onChange={handleFieldChange}
                            value={fields.refreshToken}
                            label={'NetApp Refresh Token'}
                            showFeedback={!isValidCredentials}
                            feedback={'Token has not been validated or is invalid.'}
                            placeholder="Enter NetApp refresh token"
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
                        iconclassname="fs--2"
                        style={{ marginRight: '10px' }}
                      >
                        Test and Update
                      </LoaderButton>{' '}
                      <ButtonIcon
                        onClick={cancelCreds}
                        color="falcon-default"
                        size="sm"
                        icon="times"
                        iconclassname="fs--2"
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
            <LoaderButton
              disabled={isAddingCredentials}
              block
              color="falcon-primary"
              onClick={handleSave}
              name="save-and-add"
              isLoading={isLoading}
            >
              Save changes
            </LoaderButton>
          </Col>
        </Row>
      </form>
    </>
  );
};
ConfigFormNetApp.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormNetApp;

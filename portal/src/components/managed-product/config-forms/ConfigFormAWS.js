import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useHistory } from 'react-router-dom';

import LoaderButton from '../../loader-button/LoaderButton';
import { onError } from '../../../libs/errorLib';
import { useFormFields } from '../../../libs/hooksLib';
import PropTypes from 'prop-types';
import { Row, Card, CardBody, Col, Button, FormFeedback, Label, FormGroup } from 'reactstrap';
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
import AWSFilters from '../section/AWSFilters';
import ButtonIcon from '../../common/ButtonIcon';
import { FieldGroup } from '../../../libs/formLib';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

const ConfigFormMongoDB = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();

  const [isValidCredentials, setIsValidCredentials] = useState(false);
  const [isTestingValidCredentials, setIsTestingValidCredentials] = useState(false);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);

  //  const [config, setConfig] = useState(null);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [vendorStatuses, setVendorStatuses] = useState([]);
  const [vendorEventScopes, setVendorEventScopes] = useState([]);
  const [vendorResolutionOptions, setVendorResolutionOptions] = useState([]);
  const [vendorResolutions, setVendorResolutions] = useState([]);

  const [priorityMaps, setPriorityMaps] = useState([]);

  const vendor = VENDORS[vendorId];
  const snPriorityOptions = SERVICENOW.SN_PRIORITY_OPTIONS;

  const vendorPriorityOptions = vendor.priorities;
  const vendorEventScopeOptions = vendor.eventScopes;

  const [fields, handleFieldChange] = useFormFields({
    daysBack: 60,
    awsApiHealthApiRoleArn: '',
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
            awsApiHealthApiRoleArn: '',
            vendorPriorities: [],
            vendorStatuses: [],
            vendorResolutions: [],
            snAffectedCIQuery: ''
          };

        //setConfig(settings);
        fields.daysBack = settings.daysBack;
        fields.awsApiHealthApiRoleArn = settings.awsApiHealthApiRoleArn || '';
        fields.snCompanySysId = settings.snCompanySysId;
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';

        // Set priority maps
        if (!settings.vendorPriorities) settings.vendorPriorities = [];
        if (!settings.vendorStatuses) settings.vendorStatuses = [];
        if (!settings.vendorResolutions) settings.vendorResolutions = [];
        if (!settings.vendorEventScopes) settings.vendorEventScopes = [];
        setVendorResolutions(settings.vendorResolutions);
        setVendorEventScopes(settings.vendorEventScopes);
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
      awsApiHealthApiRoleArn: fields.awsApiHealthApiRoleArn,
      snCompanySysId: fields.snCompanySysId,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      vendorPriorities,
      vendorStatuses,
      vendorEventScopes,
      type: SETTINGS.VENDOR
    };

    return BZAPIService.saveSetting(vendorId, data);
  }

  function cancelCreds() {
    fields.awsApiHealthApiRoleArn = '';
    setIsAddingCredentials(false);
  }
  async function testCreds() {
    setIsTestingValidCredentials(true);
    const data = {
      awsApiHealthApiRoleArn: fields.awsApiHealthApiRoleArn
    };
    const result = await BZAPIService.vendorTestCreds(vendorId, data);
    setIsTestingValidCredentials(false);
    if (result) {
      // valid creds
      if (!result.roleAssumed) return toast.error(`Unable to assume role.`);
      if (!result.costExplorerApiAccess) return toast.error(`Unable to access AWS Cost Explorer API.`);
      if (!result.healthApiAccess) return toast.error(`Unable to access AWS Health API.`);
      setIsValidCredentials(true);
      // setCustomers([...result.active_iq_customers]);
      setIsAddingCredentials(false);
      toast.success(`AWS Health API Role ARN validated.`);
    } else {
      toast.error(`Unable to validate AWS Health API Role ARN.`);
    }

    console.log('result', result);
  }
  async function handleSave() {
    try {
      setIsSubmitted(true);
      setIsLoading(true);
      // Validate
      if (!fields.daysBack || !fields.awsApiHealthApiRoleArn || !fields.snCompanySysId || !vendorEventScopes.length) {
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
  console.log('fields', fields);

  return (
    <>
      <form noValidate style={{ minWidth: '100%' }}>
        <Card bg={'light'} text={'dak'} className="mb-4">
          <FalconCardHeader title="Vendor settings" />
          <CardBody>
            <Row form>
              <Col lg="12">
                <FormGroup>
                  <Label>
                    AWS Health API Role ARN
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

                        {isValidCredentials || fields.awsApiHealthApiRoleArn ? (
                          <>
                            {'  '}
                            <FontAwesomeIcon icon={'check'} style={{ color: 'green', marginLeft: '10px' }} /> AWS Health
                            API Role ARN Stored
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
                            id="awsApiHealthApiRoleArn"
                            autoComplete="new-password"
                            onChange={handleFieldChange}
                            value={fields.awsApiHealthApiRoleArn}
                            label={'AWS Health API Role ARN'}
                            showFeedback={!isValidCredentials}
                            feedback={'AWS Health API Role ARN has not been validated or is invalid.'}
                            placeholder="Enter AWS Health API Role ARN"
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
                    className={!fields.secretId && !fields.awsApiHealthApiRoleArn && isSubmitted ? 'd-block' : ''}
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
            <Row>
              <Col lg="6">
                <CMDBAffectedCIQuery
                  snAffectedCIQuery={fields.snAffectedCIQuery}
                  handleFieldChange={handleFieldChange}
                  isSubmitted={isSubmitted}
                  required={false}
                />
              </Col>
            </Row>
          </CardBody>
        </Card>
        <AWSFilters
          title="AWS Filter Configuration"
          vendorEventScopeOptions={vendorEventScopeOptions}
          handleSelectChange={handleSelectChange}
          handleFieldChange={handleFieldChange}
          setVendorEventScopes={setVendorEventScopes}
          isSubmitted={isSubmitted}
          vendorEventScopes={vendorEventScopes}
        />

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
            <LoaderButton
              block
              disabled={isAddingCredentials}
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
ConfigFormMongoDB.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormMongoDB;

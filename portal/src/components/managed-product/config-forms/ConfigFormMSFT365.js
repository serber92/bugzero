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
import {Button, Card, CardBody, Col, FormFeedback, FormGroup, Label, Row} from 'reactstrap';
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
import VendorDaysBack from '../Vendor/VendorsDaysBack';

const ConfigFormMSFT365 = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();

  //  const [config, setConfig] = useState(null);
  const [isValidCredentials, setIsValidCredentials] = useState(false);
  const [isTestingValidCredentials, setIsTestingValidCredentials] = useState(false);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);
  const [vendorStatusOptions, setVendorStatusOptions] = useState([]);
  const [vendorStatuses, setVendorStatuses] = useState([]);

  const [priorityMaps, setPriorityMaps] = useState([]);

  const vendor = VENDORS[vendorId];
  const snPriorityOptions = SERVICENOW.SN_PRIORITY_OPTIONS;

  const vendorPriorityOptions = vendor.priorities;

  const [fields, handleFieldChange] = useFormFields({
    secretId: '',
    username: '',
    password: '',
    daysBack: 60,
    snCompanySysId: '60',
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
            daysBack: 60,
            snCompanySysId: '',
            vendorPriorities: [],
            vendorStatuses: [],
            snAffectedCIQuery: ''
          };

        //setConfig(settings);
        fields.daysBack = settings.daysBack;
        fields.snCompanySysId = settings.snCompanySysId;
        fields.secretId = settings.secretId;
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';

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
  function cancelCreds() {
    fields.username = '';
    fields.password = '';
    setIsAddingCredentials(false);
  }
  async function saveServiceAWSSecret() {
    const data = {
      secret: {
        username: fields.username,
        password: fields.password
      },
      vendorId: 'msft365',
      key: 'admin'
    };
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

  async function saveConfig(awsSecret) {
    // save client config
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });

    const data = {
      secretId: awsSecret.Name,
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
      setIsSubmitted(true);
      setIsLoading(true);
      // Validate
      if (!fields.snCompanySysId || !fields.daysBack) {
        console.log(fields);
        console.log('failed validation');

        setIsLoading(false);
        return;
      }

      let awsSecret;

      if (fields.username && fields.password) {
        // Updated secrets
        awsSecret = await saveServiceAWSSecret();
      } else {
        // use existing secrets
        awsSecret = { Name: fields.secretId };
      }
      console.log('awsSecret', awsSecret);
      if (!awsSecret || !awsSecret.Name) {
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

      await saveConfig(awsSecret);
      // set updated secretId
      fields.secretId = awsSecret.Name;
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
        <input type="hidden" value="prayer" />
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
                        onClick={cancelCreds}
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
                    className={!fields.secretId && !isValidCredentials && isSubmitted ? 'd-block' : ''}
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
ConfigFormMSFT365.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormMSFT365;

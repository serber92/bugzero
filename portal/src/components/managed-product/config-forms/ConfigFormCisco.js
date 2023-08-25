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

const ConfigFormCisco = ({ vendorLabel, vendorId }) => {
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
    serviceSecretId: '',
    serviceClientId: '',
    serviceClientSecret: '',
    supportSecretId: '',
    supportClientId: '',
    supportClientSecret: '',
    daysBack: '60',
    snCompanySysId: '60',
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
            serviceSecretId: '',
            supportSecretId: '',
            secretId: '',
            snCompanySysId: '',
            vendorPriorities: [],
            vendorStatuses: [],
            snAffectedCIQuery: ''
          };

        //setConfig(settings);
        fields.daysBack = settings.daysBack;
        fields.snCompanySysId = settings.snCompanySysId;
        fields.serviceSecretId = settings.serviceSecretId;
        fields.supportSecretId = settings.supportSecretId;
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
  }, [fields.supportSecretId, fields.serviceSecretId]);

  async function testCreds() {
    setIsTestingValidCredentials(true);
    const data = {
      supportApiClientId: fields.supportClientId,
      supportApiClientSecret: fields.supportClientSecret,
      serviceApiClientId: fields.serviceClientId,
      serviceApiClientSecret: fields.serviceClientSecret
    };
    const result = await BZAPIService.vendorTestCreds(vendorId, data);
    setIsTestingValidCredentials(false);
    if (result && result.completed) {
      // valid creds
      console.log('result.active_iq_customers', result.active_iq_customers);
      fields.refreshToken = result.refresh_token;
      setIsValidCredentials(true);
      setIsAddingCredentials(false);
      toast.success(`Credentials validated.`);
    } else {
      toast.error(`Unable to validate credentials.`);
    }

    console.log('result', result);
  }

  async function saveServiceAWSSecret() {
    const data = {
      secret: {
        ClientId: fields.serviceClientId,
        ClientSecret: fields.serviceClientSecret
      },
      vendorId: 'cisco',
      key: 'serviceApi'
    };
    // service api secret
    return BZAPIService.createOrUpdateAWSSecret(data);
    // if (fields.serviceSecretId) {
    //   data.secretId = fields.serviceSecretId;
    //   return BZAPIService.updateAWSSecret(data);
    // } else return BZAPIService.createAWSSecret(data);
  }

  async function saveSupportAWSSecret() {
    const data = {
      secret: {
        ClientId: fields.supportClientId,
        ClientSecret: fields.supportClientSecret
      },
      vendorId: 'cisco',
      key: 'supportApi'
    };

    // support api secret
    return BZAPIService.createOrUpdateAWSSecret(data);
  }
  async function saveConfig(serviceSecret, supportSecret) {
    // save client config
    const vendorPriorities = priorityMaps.map(mapping => {
      return {
        vendorPriority: mapping.vendorPriority.value,
        snPriority: mapping.snPriority.value
      };
    });

    const data = {
      daysBack: fields.daysBack,
      serviceSecretId: serviceSecret.Name,
      supportSecretId: supportSecret.Name,
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
      if (!fields.daysBack || !fields.snCompanySysId) {
        console.log(fields);
        console.log('failed validation');

        setIsLoading(false);
        return;
      }
      // Validate status
      if (!vendorStatuses.length) {
        console.log('Missing status');
        setIsLoading(false);
        return;
      }
      // Validate priorities
      if (!priorityMaps.length) {
        console.log('Missing priorities');
        setIsLoading(false);
        return;
      }
      // Validate Secrets

      if (!fields.serviceSecretId || !fields.supportSecretId) {
        if (
          !fields.serviceClientId ||
          !fields.serviceClientSecret ||
          !fields.supportClientId ||
          !fields.supportClientSecret
        ) {
          console.log('misisng secret');
          setIsLoading(false);
          return;
        }
      }

      let serviceSecret, supportSecret;

      if (
        fields.serviceClientSecret &&
        fields.serviceClientId &&
        fields.supportClientId &&
        fields.supportClientSecret
      ) {
        // Updated secrets
        serviceSecret = await saveServiceAWSSecret();
        supportSecret = await saveSupportAWSSecret();
      } else {
        // use existin secrets
        serviceSecret = { Name: fields.serviceSecretId };
        supportSecret = { Name: fields.supportSecretId };
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

      await saveConfig(serviceSecret, supportSecret);
      // set updated secretId
      fields.serviceSecretId = serviceSecret.Name;
      fields.supportSecretId = supportSecret.Name;
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
                    Cisco API Credentials
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

                        {(fields.serviceSecretId && fields.supportSecretId) || isValidCredentials ? (
                          <>
                            {'  '}
                            <FontAwesomeIcon icon={'check'} style={{ color: 'green', marginLeft: '10px' }} /> Cisco API
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
                            id="serviceClientId"
                            autoComplete="new-password"
                            onChange={handleFieldChange}
                            value={fields.serviceClientId}
                            label={'Service API Client ID'}
                            showFeedback={!fields.serviceClientId && isSubmitted}
                            feedback={'Please specify a service client id.'}
                            placeholder="Enter service api client id"
                            style={{ marginBottom: '10px' }}
                            required
                          />{' '}
                          <FieldGroup
                            type="serviceClientSecret"
                            id="serviceClientSecret"
                            label={'Service API Client Secret'}
                            autoComplete="new-serviceClientSecret"
                            placeholder="Enter service api client secret"
                            onChange={handleFieldChange}
                            value={fields.serviceClientSecret}
                            showFeedback={!fields.serviceClientSecret && isSubmitted}
                            feedback={'Please specify a service api client secret.'}
                            required
                          />
                        </Col>
                        <Col lg="6">
                          <FieldGroup
                            type="text"
                            id="supportClientId"
                            autoComplete="new-password"
                            onChange={handleFieldChange}
                            value={fields.supportClientId}
                            label={'Support API Client ID'}
                            showFeedback={!fields.supportClientId && isSubmitted}
                            feedback={'Please specify a support client id.'}
                            placeholder="Enter support api client id"
                            style={{ marginBottom: '10px' }}
                            required
                          />
                          <FieldGroup
                            type="supportClientSecret"
                            id="supportClientSecret"
                            label={'Support API Client Secret'}
                            autoComplete="new-supportClientSecret"
                            placeholder="Enter support api client secret"
                            onChange={handleFieldChange}
                            value={fields.supportClientSecret}
                            showFeedback={!fields.supportClientSecret && isSubmitted}
                            feedback={'Please specify a support api client secret.'}
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
                    className={
                      !fields.serviceSecretId &&
                      !fields.supportSecretId &&
                      !fields.serviceClientId &&
                      !fields.serviceClientSecret &&
                      !fields.supportClientId &&
                      !fields.supportClientSecret &&
                      isSubmitted
                        ? 'd-block'
                        : ''
                    }
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
            <LoaderButton block color="falcon-primary" onClick={handleSave} name="save-and-add" isLoading={isLoading}>
              Save changes
            </LoaderButton>
          </Col>
        </Row>
      </form>
    </>
  );
};
ConfigFormCisco.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormCisco;

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
import {
  Row,
  Card,
  CardBody,
  FormGroup,
  Label,
  FormFeedback,
  Col,
  Button,
  ListGroup,
  ListGroupItem,
  CardTitle,
  CardText
} from 'reactstrap';
import Loader from '../../common/Loader';
import FalconCardHeader from '../../common/FalconCardHeader';
import BZAPIService from '../../../services/BZAPIService';
import CMDBCompany from '../ServiceNow/CMDBCompany';
import ProductPriority from '../section/ProductPriority';
import CMDBAffectedCIQuery from '../ServiceNow/CMDBAffectedCIQuery';
import VendorDaysBack from '../Vendor/VendorsDaysBack';

// constants
import SETTINGS from '../../../constants/settings';
import SERVICENOW from '../../../constants/servicenow';

const ConfigFormVmware = ({
  vendorLabel,
  vendorId,
  vendorPriorityOptions,
  vendorStatusOptions,
  vendorResolutionOptions,
  vendorBugCategories,
  vendorBugTypes
}) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();

  const [isValidCredentials, setIsValidCredentials] = useState(false);
  const [isTestingValidCredentials, setIsTestingValidCredentials] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);
  const [vendorStatuses, setVendorStatuses] = useState([]);
  const [vendorCategories, setVendorCategories] = useState([]);
  const [vendorTypes, setVendorTypes] = useState([]);
  const [priorityMaps, setPriorityMaps] = useState([]);
  const snPriorityOptions = SERVICENOW.SN_PRIORITY_OPTIONS;
  const [fields, handleFieldChange] = useFormFields({
    secretId: '',
    username: '',
    password: '',
    daysBack: '',
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
            daysBack: '',
            snCompanySysId: '',
            vendorPriorities: [],
            vendorStatuses: [],
            vendorCategories: [],
            vendorTypes: [],
            snAffectedCIQuery: ''
          };

        fields.daysBack = settings.daysBack || '';
        fields.snCompanySysId = settings.snCompanySysId || '';
        fields.secretId = settings.secretId || '';
        fields.snAffectedCIQuery = settings.snAffectedCIQuery || '';

        if (settings.accountOrgs) setOrganizations(settings.accountOrgs);

        // Set priority maps
        if (!settings.vendorPriorities) settings.vendorPriorities = [];
        if (!settings.vendorStatuses) settings.vendorStatuses = [];
        if (!settings.vendorCategories) settings.vendorCategories = [];
        if (!settings.vendorTypes) settings.vendorTypes = [];
        setVendorStatuses(settings.vendorStatuses);
        setVendorCategories(settings.vendorCategories);
        setVendorTypes(settings.vendorTypes);

        const priorityMaps = settings.vendorPriorities.map(priority => {
          const result = {
            vendorPriority: vendorPriorityOptions.find(e => e.value === priority.vendorPriority),
            snPriority: snPriorityOptions.find(e => e.value === priority.snPriority)
          };

          return result;
        });
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
        username: fields.username,
        password: fields.password
      },
      vendorId: 'vmware',
      key: 'skylineAuth'
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
      fields.refreshToken = result.refresh_token;
      setIsValidCredentials(true);
      setOrganizations([...result.account_orgs]);
      setIsAddingCredentials(false);
      toast.success('Credentials successfully validated.');
    } else {
      toast.error('Credentials failed validation.');
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
      daysBack: fields.daysBack,
      snCompanySysId: fields.snCompanySysId,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      accountOrgs: organizations,

      vendorPriorities,
      vendorStatuses,
      vendorCategories,
      vendorTypes,
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

      // Validate Secrets

      if (!fields.secretId) {
        if (!fields.username || !fields.password) {
          console.log('misisng secret');
          setIsLoading(false);
          return;
        }
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
    organizations[index].disabled = disabled;

    setOrganizations([...organizations]);
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
            <CardTitle>Manage your {vendorLabel} settings</CardTitle>
            <CardText>Configure your preferences for {vendorLabel}</CardText>

            <Row form>
              <Col lg="12">
                <FormGroup>
                  <Label>
                    VMware API Credentials
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
                            <FontAwesomeIcon icon={'check'} style={{ color: 'green', marginLeft: '10px' }} /> VMware
                            Credentials Stored
                            <Row form>
                              <Col lg="12">
                                <FormGroup>
                                  <Label>
                                    VMware Organizations
                                    <span style={{ color: '#bd472a' }}>*</span>
                                  </Label>
                                  <ListGroup>
                                    {organizations.map(({ orgId, name, disabled }, index) => {
                                      console.log(`${name} ${disabled}`);

                                      return (
                                        <ListGroupItem key={orgId}>
                                          <input
                                            type="checkbox"
                                            checked={!disabled}
                                            onChange={() => handleToggleCustomer(index, disabled ? 0 : 1)}
                                          />{' '}
                                          {name}
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
                            id="username"
                            autoComplete="new-password"
                            onChange={handleFieldChange}
                            value={fields.username}
                            label={'VMware username'}
                            showFeedback={!fields.username && isSubmitted}
                            feedback={'Please specify username.'}
                            placeholder="Enter VMware username"
                            style={{ marginBottom: '10px' }}
                            required
                          />
                        </Col>
                        <Col lg="6">
                          <FieldGroup
                            type="password"
                            id="password"
                            label={'VMware Password'}
                            autoComplete="new-password"
                            placeholder="Enter VMware password"
                            onChange={handleFieldChange}
                            value={fields.password}
                            showFeedback={!fields.password && isSubmitted}
                            feedback={'Please specify a password.'}
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
                    className={!fields.secretId && !fields.username && !fields.password && isSubmitted ? 'd-block' : ''}
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
          vendorBugCategories={vendorBugCategories}
          vendorBugTypes={vendorBugTypes}
          handleSelectChange={handleSelectChange}
          setVendorStatuses={setVendorStatuses}
          setVendorCategories={setVendorCategories}
          setVendorTypes={setVendorTypes}
          vendorStatuses={vendorStatuses}
          vendorCategories={vendorCategories}
          vendorTypes={vendorTypes}
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
ConfigFormVmware.propTypes = {
  vendorPriorityOptions: PropTypes.array,
  vendorStatusOptions: PropTypes.array,
  vendorResolutionOptions: PropTypes.array,
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormVmware;

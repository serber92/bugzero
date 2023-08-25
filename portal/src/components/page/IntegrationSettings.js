import React, {useEffect, useState} from 'react';
import {useHistory} from 'react-router-dom';
import {Badge, Button, Card, CardBody, Col, FormGroup, Label, Row} from 'reactstrap';
import {toast} from 'react-toastify';

import Loader from '../common/Loader';
import FalconCardHeader from '../common/FalconCardHeader';
// services
import SNAPIService from '../../services/SNAPIService';
import BZAPIService from '../../services/BZAPIService';
//libs
import {useFormFields} from '../../libs/hooksLib';
import {onError} from '../../libs/errorLib';
import {FieldGroup} from '../../libs/formLib';
// constants
import SETTINGS from '../../constants/settings';
import Heading from '../common/Heading';
import ButtonIcon from '../common/ButtonIcon';
import LoaderButton from '../loader-button/LoaderButton';
import Divider from '../common/Divider';
import { valid } from 'joi';

const ConfigServiceNow = () => {
  const [isValidUrl, setIsValidUrl] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [connected, setConnected] = useState(null);
  const [isAddingCredentials, setIsAddingCredentials] = useState(false);
  const [fields, handleFieldChange] = useFormFields({
    snApiUrl: '',
    secretId: '',
    snAuthToken: '',
    user: '',
    pass: ''
  });
  const history = useHistory();
  useEffect(() => {
    async function onLoad() {
      try {
        // Set Managed product if exists
        let settings = await BZAPIService.getSetting(SETTINGS.SERVICE_NOW);
        if (!settings)
          settings = {
            secretId: '',
            snApiUrl: '',
            snAuthToken: ''
          };
        fields.secretId = settings.secretId;
        fields.snApiUrl = settings.snApiUrl;
        fields.snAuthToken = settings.snAuthToken;
        setIsLoading(false);
      } catch (e) {
        onError(e);
      }
    }

    onLoad();
  }, [fields.secretId]);
  async function saveAWSSecret() {
    const data = {
      secret: {
        user: fields.user,
        pass: fields.pass
      },
      vendorId: 'servicenow',
      key: 'snAuth'
    };
    // service api secret
    return BZAPIService.createOrUpdateAWSSecret(data);
  }

  async function saveConfig(secret) {
    const data = {
      secretId: secret.Name,
      snApiUrl: fields.snApiUrl,
      type: 'global'
    };

    return BZAPIService.saveSetting(SETTINGS.SERVICE_NOW, data);
  }
  async function handleSave() {
    try {
      // validate url
      const validUrl = fields.snApiUrl.match(
        /^(http(s)?:\/\/)[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$/
      );
      console.log('validUrl', validUrl);
      if (!validUrl) setIsValidUrl(false);
      else setIsValidUrl(true);
      setIsSubmitted(true);
      setIsLoading(true);
      // Validate
      if (!fields.snApiUrl || !validUrl) {
        setIsLoading(false);

        return;
      }

      // Validate Secrets
      if (!fields.secretId) {
        if (!fields.user || !fields.pass) {
          console.log('misisng secret');
          setIsLoading(false);
          return;
        }
      }

      let secret;

      if (fields.user && fields.pass) {
        // Updated secrets
        secret = await saveAWSSecret();
      } else {
        // use existing secrets
        secret = { Name: fields.secretId };
      }
      console.log('secret', secret);
      if (!secret || !secret.Name) {
        setIsLoading(false);
        throw Error('Missing Secret');
      }

      await saveConfig(secret);
      setIsLoading(false);
      setIsSubmitted(false);
      toast.success(`Settings Saved!`);
    } catch (e) {
      setIsLoading(false);
      toast.error('Failed to save.');
      console.log('e', e);
    }
    // Go back to listing
  }

  function updateToken() {
    const btoaCredentials = btoa(`${fields.user}:${fields.pass}`);
    console.log(`${fields.user}:${fields.pass}`);
    console.log(btoaCredentials);

    fields.snAuthToken = btoaCredentials;
    setIsAddingCredentials(false);
  }
  async function checkConnection() {
    console.log('checkCon', SNAPIService);

    const originalBaseUrl = SNAPIService.apiClient.getBaseURL();
    console.log('origin', originalBaseUrl);

    try {
      // Update base url
      console.log('fields.snApiUrl', fields.snApiUrl);

      SNAPIService.apiClient.setBaseURL(fields.snApiUrl);
      const response = await SNAPIService.connectionTest(fields.snAuthToken);
      console.log('response', response);
      if (!response.ok) {
        setConnected(`Error: ${response.status} - ${response.problem}`);
      } else {
        setConnected('success');
      }
      // Revert base url
      SNAPIService.apiClient.setBaseURL(originalBaseUrl);
    } catch (e) {
      console.log('e', e);
      // Revert base url
      SNAPIService.apiClient.setBaseURL(originalBaseUrl);
      setConnected(`Error: ${e}`);
    }
  }
  return (
    <>
      <Heading
        title="ServiceNow Configuration"
        subtitle="Specify your ServiceNow configuration"
        className="mb-4 mt-3"
        icon="cog"
      />

      <Card>
        <FalconCardHeader title="General Settings" />
        <CardBody className="fs--1">
          {isLoading ? (
            <Loader />
          ) : (
            <>
              <FormGroup lg="5">
                <FieldGroup
                  type="text"
                  label="ServiceNow URL"
                  id="snApiUrl"
                  onChange={handleFieldChange}
                  value={fields.snApiUrl}
                  placeholder="Enter URL"
                  style={{ marginBottom: '10px' }}
                  help="Eg. https://my-service-now-instance.com"
                  feedback="Please specify a valid url starting with http or https."
                  showFeedback={!isValidUrl && isSubmitted}
                />
              </FormGroup>
              <Row form>
                <Col lg="12">
                  <FormGroup>
                    {!isAddingCredentials ? (
                      <>
                        <FieldGroup
                          label="ServiceNow API Credentials"
                          type="password"
                          id="snAuthToken"
                          onChange={handleFieldChange}
                          value={fields.snAuthToken}
                          readOnly
                          placeholder="Specify credentials"
                          style={{ marginBottom: '10px' }}
                          feedback="Please specify credentials."
                          showFeedback={!fields.secretId && isSubmitted}
                        />
                        <ButtonIcon
                          onClick={() => setIsAddingCredentials(true)}
                          color="falcon-default"
                          size="sm"
                          icon="plus"
                          iconClassName="fs--2"
                        >
                          Set Credentials
                        </ButtonIcon>
                      </>
                    ) : (
                      <>
                        <Row>
                          <Col lg="6">
                            <FieldGroup
                              type="text"
                              label="ServiceNow API Credentials"
                              id="user"
                              onChange={handleFieldChange}
                              value={fields.user}
                              placeholder="Enter username"
                              style={{ marginBottom: '10px' }}
                            />
                          </Col>
                          <Col lg="6">
                            <FieldGroup
                              type="text"
                              label="&nbsp;"
                              id="pass"
                              placeholder="Enter password"
                              onChange={handleFieldChange}
                              value={fields.pass}
                              help="We will auto-generate a token based off the credentials you
													enter."
                            />
                          </Col>
                        </Row>
                        <br />
                        <ButtonIcon
                          onClick={updateToken}
                          color="falcon-default"
                          size="sm"
                          icon="check"
                          iconClassName="fs--2"
                          style={{ marginRight: '10px' }}
                        >
                          Update
                        </ButtonIcon>{' '}
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
                  </FormGroup>
                </Col>
              </Row>
              <Row form>
                <Col lg="12">
                  <Divider className="mt-4">verify settings above</Divider>

                  <FormGroup>
                    <Label>Connection Status</Label>
                    <div>
                      <ButtonIcon
                        disabled={!fields.snApiUrl || !fields.snAuthToken}
                        onClick={checkConnection}
                        color="falcon-default"
                        size="sm"
                        icon="plug"
                        iconClassName="fs--2"
                        style={{ marginRight: '10px' }}
                      >
                        Test Connection
                      </ButtonIcon>
                      {connected === 'success' && <Badge variant="success">Success</Badge>}
                      {connected && connected !== 'success' && <Badge variant="danger">{connected}</Badge>}
                    </div>
                  </FormGroup>
                </Col>
              </Row>
            </>
          )}
        </CardBody>
      </Card>
      <Row className="flex-between-center" style={{ marginTop: '40px' }}>
        <Col xs="auto">
          <Button
            block
            color="falcon-danger"
            onClick={() => {
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
    </>
  );
};

export default ConfigServiceNow;

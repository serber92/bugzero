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
import CMDBAffectedCIQuery from '../ServiceNow/CMDBAffectedCIQuery';
import CMDBCompany from '../ServiceNow/CMDBCompany';
import VendorDaysBack from '../Vendor/VendorsDaysBack';
// constants
import SETTINGS from '../../../constants/settings';

const ConfigFormHPE = ({ vendorLabel, vendorId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const history = useHistory();

  const [fields, handleFieldChange] = useFormFields({
    daysBack: '',
    snCompanySysId: '',
    snAffectedCIQuery: ''
  });

  useEffect(() => {
    async function onLoad() {
      console.log('onload');
      try {
        let settings = (await BZAPIService.getSetting(vendorId)) || {};
        // Init defaults
        if (!settings)
          settings = {
            daysBack: '60',
            snCompanySysId: '',
            snAffectedCIQuery: ''
          };

        //setConfig(settings);
        fields.daysBack = settings.daysBack | '';
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

    const data = {
      daysBack: fields.daysBack,
      snCompanySysId: fields.snCompanySysId,
      snAffectedCIQuery: fields.snAffectedCIQuery,
      type: SETTINGS.VENDOR
    };

    return BZAPIService.saveSetting(vendorId, data);
  }

  async function handleSave() {
    try {
      setIsLoading(true);
      setIsSubmitted(true);
      // Validate
      if (!fields.daysBack || !fields.snCompanySysId) {
        console.log('error');
        setIsLoading(false);
        return;
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
ConfigFormHPE.propTypes = {
  vendorLabel: PropTypes.string,
  vendorId: PropTypes.string
};
export default ConfigFormHPE;

import React from 'react';
import { Card, Col, CardBody, CardText, CardTitle, Row, FormGroup, Label, FormFeedback } from 'reactstrap';
import Select from 'react-select';
import FalconCardHeader from '../../common/FalconCardHeader';

// Managed product components
import PropTypes from 'prop-types';

export default function AWSFilters({
  handleSelectChange,
  vendorEventScopes = [],
  setVendorEventScopes,
  vendorEventScopeOptions = [],
  isSubmitted,
  title
}) {
  // Prioritiy
  return (
    <Card bg={'light'} text={'dark'} style={{}} className="mb-4">
      <FalconCardHeader title={title} />
      <CardBody>
        <>
          <CardTitle>Select AWS event scopes to Monitor</CardTitle>
          <CardText>Select multiple entries if necessary</CardText>
          <Row form>
            <Col lg="5">
              <FormGroup>
                <Label>
                  Event scopes<span style={{ color: '#bd472a' }}>*</span>
                </Label>
                <Select
                  defaultValue={[]}
                  isMulti
                  name="colors"
                  onChange={e => handleSelectChange(e, setVendorEventScopes)}
                  value={vendorEventScopeOptions.filter(vso => {
                    return vendorEventScopes.indexOf(vso.value) !== -1;
                  })}
                  options={vendorEventScopeOptions}
                  className="basic-multi-select"
                  classNamePrefix="select"
                />
                <FormFeedback
                  className={
                    isSubmitted && vendorEventScopeOptions.length && !vendorEventScopes.length ? 'd-block' : ''
                  }
                  type="invalid"
                >
                  Please select a event scope.
                </FormFeedback>
              </FormGroup>
            </Col>
          </Row>
          <br />
        </>
      </CardBody>
    </Card>
  );
}
AWSFilters.defaultProps = {
  vendorStatusOptions: [],
  vendorResolutionOptions: [],
  vendorStatuses: [],
  vendorResolutions: []
};

AWSFilters.propTypes = {
  vendorEventScopeOptions: PropTypes.array,
  handleSelectChange: PropTypes.func,
  setVendorEventScopes: PropTypes.func,
  vendorEventScopes: PropTypes.array,
  isSubmitted: PropTypes.bool,
  title: PropTypes.string
};

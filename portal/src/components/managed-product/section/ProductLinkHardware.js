import React from 'react';
import PropTypes from 'prop-types';
import { Card, CardBody, CardHeader, CardTitle, CardText, Row, FormGroup, Label, FormFeedback, Col } from 'reactstrap';
import Select from 'react-select';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEquals } from '@fortawesome/free-solid-svg-icons';
import FalconCardHeader from '../../common/FalconCardHeader';

export default function ProductLinkHardware({
  snProductOptions,
  snProductId,
  handleSelectChange,
  setSnProductId,
  setVendorProductId,
  isSubmitted,
  vendor,
  vendorProductId,
  vendorProductOptions
}) {
  return (
    <Card bg={'light'} text={'dak'} className="mb-4">
      <FalconCardHeader title="Product link" />

      <CardBody>
        <Row form>
          <Col lg="5">
            <FormGroup>
              <Label>
                ServiceNow CMDB<span style={{ color: '#bd472a' }}>*</span>
              </Label>
              <Select
                value={snProductOptions.filter(option => option.value === snProductId)}
                onChange={e => handleSelectChange(e, setSnProductId)}
                options={snProductOptions}
              />
              <FormFeedback className={!snProductId && isSubmitted ? 'd-block' : ''} type="invalid">
                Please select a product model.
              </FormFeedback>
            </FormGroup>
          </Col>
          <Col lg="1">
            <FormGroup style={{ textAlign: 'center', marginTop: '38px' }}>
              <FontAwesomeIcon icon={faEquals} />
            </FormGroup>
          </Col>
          <Col lg="5">
            <FormGroup>
              <Label>
                BugZero<span style={{ color: '#bd472a' }}>*</span>
              </Label>

              {vendor.vendorId === 'hpe' && (
                <>
                  <Select
                    value={vendorProductOptions.filter(option => option.value === vendorProductId)}
                    onChange={e => handleSelectChange(e, setVendorProductId)}
                    options={vendorProductOptions}
                  />
                  <FormFeedback className={!vendorProductId && isSubmitted ? 'd-block' : ''} type="invalid">
                    Please select a product model.
                  </FormFeedback>
                </>
              )}
            </FormGroup>
          </Col>
          <Col lg="1">
            <FormGroup style={{ textAlign: 'center', marginTop: '38px' }} />
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
}

ProductLinkHardware.propTypes = {
  snProductOptions: PropTypes.array,
  vendorProductOptions: PropTypes.array,
  snProductId: PropTypes.string,
  vendorProductId: PropTypes.string,
  handleSelectChange: PropTypes.func,
  setSnProductId: PropTypes.func,
  setVendorProductId: PropTypes.func,
  isSubmitted: PropTypes.bool,
  vendor: PropTypes.object
};

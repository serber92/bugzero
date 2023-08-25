import React from 'react';
import PropTypes from 'prop-types';
import { Card, Col, FormFeedback, CardHeader, CardText, CardBody, CardTitle, Row, FormGroup, Label } from 'reactstrap';
import Select from 'react-select';
import FalconCardHeader from '../../common/FalconCardHeader';

export default function ProductLinkSoftware({
  snProductOptions,
  snProductId,
  handleSelectChange,
  setSnProductId,
  setVendorProductId,
  isSubmitted
}) {
  console.log('xsnProductOptions', snProductOptions);
  console.log('snProductId', typeof snProductId);
  return (
    <Card bg={'light'} text={'dak'} style={{}} className="mb-4">
      <FalconCardHeader title="Operating System" />
      <CardBody>
        <CardTitle>Select Operating System to Manage</CardTitle>
        <CardText>
          Links ServiceNow CMDB Operating Systems to BugZero supported Operating Systems (e.g. Red Hat Enterprise Linux
          8)
        </CardText>
        <Row form>
          <Col lg="5">
            <FormGroup>
              <Label>
                ServiceNow CMDB<span style={{ color: '#bd472a' }}>*</span>
              </Label>
              <Select
                value={snProductOptions.filter(option => option.value === parseInt(snProductId))}
                onChange={e => {
                  console.log('snProductOptions', snProductOptions);
                  handleSelectChange(e, setSnProductId);
                  handleSelectChange(e, setVendorProductId);
                }}
                options={snProductOptions}
              />
              <FormFeedback className={!snProductId && isSubmitted ? 'd-block' : ''} type="invalid">
                Please select a product model.
              </FormFeedback>
            </FormGroup>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
}

ProductLinkSoftware.propTypes = {
  snProductOptions: PropTypes.array,
  snProductId: PropTypes.string,
  handleSelectChange: PropTypes.func,
  setSnProductId: PropTypes.func,
  setVendorProductId: PropTypes.func,
  isSubmitted: PropTypes.bool
};

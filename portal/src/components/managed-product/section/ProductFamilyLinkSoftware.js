import React from 'react';
import PropTypes from 'prop-types';
import { Card, Col, FormFeedback, CardHeader, CardBody, CardTitle, CardText, Row, FormGroup, Label } from 'reactstrap';
import Select from 'react-select';
import FalconCardHeader from '../../common/FalconCardHeader';

export default function ProductFamilyLinkSoftware({
  vendorProductFamilyOptions,
  vendorProductFamilyId,
  handleSelectChange,
  setVendorProductFamilyId,
  isSubmitted
}) {
  return (
    <Card bg={'light'} text={'dak'} style={{}} className="mb-4">
      <FalconCardHeader title="Product family" />
      <CardBody>
        <CardTitle>Select Product Family to Manage</CardTitle>
        <CardText>Links ServiceNow to BugZero supported Product Families (e.g. SQL Server)</CardText>
        <Row form>
          <Col lg="5">
            <FormGroup>
              <Label>
                ServiceNow CMDB<span style={{ color: '#bd472a' }}>*</span>
              </Label>
              <Select
                value={vendorProductFamilyOptions.filter(option => option.value === vendorProductFamilyId)}
                onChange={e => {
                  handleSelectChange(e, setVendorProductFamilyId);
                }}
                options={vendorProductFamilyOptions}
              />
              <FormFeedback className={!vendorProductFamilyId && isSubmitted ? 'd-block' : ''} type="invalid">
                Please select a product family.
              </FormFeedback>
            </FormGroup>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
}

ProductFamilyLinkSoftware.propTypes = {
  vendorProductFamilyOptions: PropTypes.array,
  vendorProductFamilyId: PropTypes.string,
  handleSelectChange: PropTypes.func,
  setVendorProductFamilyId: PropTypes.func,
  isSubmitted: PropTypes.bool
};

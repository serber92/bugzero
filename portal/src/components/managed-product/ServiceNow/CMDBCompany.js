import React from 'react';
import { FieldGroup } from '../../../libs/formLib';
import PropTypes from 'prop-types';

export default function CMDBCompany({ snCompanySysId, handleFieldChange, isSubmitted }) {
  return (
    <FieldGroup
      type="text"
      id="snCompanySysId"
      label="Vendor System ID (ServiceNow)"
      onChange={handleFieldChange}
      value={snCompanySysId}
      showFeedback={!snCompanySysId && isSubmitted}
      feedback="Please specify a ServiceNow sys_id."
      placeholder="Enter sys_id"
      style={{ marginBottom: '10px' }}
      help="Eg. d15d02f4db365010d2f837823996190d"
      required
    />
  );
}
CMDBCompany.propTypes = {
  snCompanySysId: PropTypes.string,
  handleFieldChange: PropTypes.func,
  isSubmitted: PropTypes.bool
};

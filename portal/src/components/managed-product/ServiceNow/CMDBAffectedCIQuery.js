import React from 'react';
import { FieldGroup } from '../../../libs/formLib';
import PropTypes from 'prop-types';

export default function CMDBAffectedCIQuery({ snAffectedCIQuery, handleFieldChange, required = null, isSubmitted }) {
  return (
    <FieldGroup
      required={required}
      type="text"
      id="snAffectedCIQuery"
      label="CMDB Affected CI Query"
      showFeedback={isSubmitted && !snAffectedCIQuery && required}
      feedback="Please specify a affected CI query."
      onChange={handleFieldChange}
      value={snAffectedCIQuery}
      placeholder="Eg. install_status=1^operational_status=1."
      style={{ marginBottom: '10px' }}
      help="Note: Updating this value may result in adding or removing existing managed products and their associated bugs."
    />
  );
}
CMDBAffectedCIQuery.propTypes = {
  snAffectedCIQuery: PropTypes.string,
  handleFieldChange: PropTypes.func,
  isSubmitted: PropTypes.bool,
  required: PropTypes.bool
};

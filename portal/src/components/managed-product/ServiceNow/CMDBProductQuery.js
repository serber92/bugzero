import React from 'react';
import { FieldGroup } from '../../../libs/formLib';
import PropTypes from 'prop-types';

export default function CMDBProductQuery({ snProductQuery, handleFieldChange, isSubmitted }) {
  return (
    <FieldGroup
      type="text"
      id="snProductQuery"
      label="Table API Product CMDB Query"
      onChange={handleFieldChange}
      value={snProductQuery}
      showFeedback={!snProductQuery && isSubmitted}
      feedback="Please specify a product query."
      placeholder="Enter product query"
      style={{ marginBottom: '10px' }}
      help="Eg. cmdb_ci?sysparm_query=osLIKEVendor&amp;sysparm_fields=os,os_version"
      required
    />
  );
}
CMDBProductQuery.propTypes = {
  snProductQuery: PropTypes.string,
  handleFieldChange: PropTypes.func,
  isSubmitted: PropTypes.bool
};

import React from 'react';
import { FieldGroup } from '../../../libs/formLib';
import PropTypes from 'prop-types';

export default function VendorDaysBack({ daysBack, handleFieldChange, isSubmitted }) {
  return (
    <FieldGroup
      type="number"
      id="daysBack"
      step="1"
      pattern="\d+"
      label="Days to look back for bugs"
      showFeedback={!daysBack && isSubmitted}
      feedback="Please specify a number."
      onChange={handleFieldChange}
      value={daysBack}
      placeholder="Enter number"
      style={{ marginBottom: '10px' }}
      help="Eg. 365 to look back one year."
      required
    />
  );
}
VendorDaysBack.propTypes = {
  daysBack: PropTypes.string,
  handleFieldChange: PropTypes.func,
  isSubmitted: PropTypes.bool
};

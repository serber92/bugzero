import React from 'react';
import PropTypes from 'prop-types';
import { Col, FormText, FormFeedback, FormGroup, Input, Label, Row } from 'reactstrap';

export function FieldGroup({ id, label, showFeedback = false, required = false, feedback, help, lg, ...props }) {
  return (
    <Row form>
      <Col sm tag={FormGroup}>
        {label ? (
          <Label>
            {label}
            {required ? <span style={{ color: '#bd472a' }}>*</span> : null}
          </Label>
        ) : null}
        <Input id={id} {...props} />
        {help && <FormText color="muted">{help}</FormText>}
        <FormFeedback className={showFeedback ? 'd-block' : ''}>{feedback}</FormFeedback>
      </Col>
    </Row>
  );
}

FieldGroup.propTypes = {
  id: PropTypes.string,
  lg: PropTypes.string,
  label: PropTypes.string,
  help: PropTypes.string,
  feedback: PropTypes.string,
  showFeedback: PropTypes.bool,
  required: PropTypes.bool
};

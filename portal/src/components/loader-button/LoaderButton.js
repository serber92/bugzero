import React from 'react';
import { Button } from 'reactstrap';
import './LoaderButton.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import PropTypes from 'prop-types';

export default function LoaderButton({ isLoading, className = '', disabled = false, ...props }) {
  return (
    <Button className={`LoaderButton ${className}`} disabled={disabled || isLoading} {...props}>
      {isLoading ? <FontAwesomeIcon icon={faSpinner} pulse /> : props.children}
    </Button>
  );
}

LoaderButton.propTypes = {
  isLoading: PropTypes.bool,
  className: PropTypes.string,
  disabled: PropTypes.bool,
  children: PropTypes.string
};

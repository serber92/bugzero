import React from 'react';
import './Loading.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

export default function LoaderButton() {
  return (
    <div className="loading">
      <FontAwesomeIcon icon={faSpinner} pulse />
    </div>
  );
}

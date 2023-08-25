import React from 'react';
import PropTypes from 'prop-types';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Card, CardBody, CardFooter } from 'reactstrap';
import Background from '../common/Background';

const getContentClassNames = color => {
  const contentClassNames = 'display-12 fs-12 mb-12 font-weight-normal text-sans-serif';
  return contentClassNames;
};

const CardSummary = ({ title, rate, linkText, to, color, children, message }) => {
  let icon = 'exclamation';
  switch (color) {
    case 'success':
      icon = 'check';

      break;
    case 'info':
      icon = 'clock';

      break;
    case 'warning':
      icon = 'exclamation';

      break;

    default:
      break;
  }
  return (
    <Card className="mb-2 overflow-hidden" style={{ minWidth: '24rem' }}>
      <Background className={`bg-card`} />
      <CardBody className="position-relative">
        <h6 className={`text-${color} `}>
          {title}
          <FontAwesomeIcon icon={icon} color={color} transform="down-1.5" className="ml-1" />
        </h6>
        <div className={getContentClassNames(color)}>
          {children}
          <div className={`text-muted`}>{message}</div>
        </div>
      </CardBody>
    </Card>
  );
};

CardSummary.propTypes = {
  title: PropTypes.string.isRequired,
  message: PropTypes.string,
  rate: PropTypes.string,
  linkText: PropTypes.string,
  to: PropTypes.string,
  color: PropTypes.string,
  children: PropTypes.node
};

CardSummary.defaultProps = {
  linkText: 'See all',
  to: '#!',
  color: 'primary'
};

export default CardSummary;

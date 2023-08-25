import React, { Fragment, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Button } from 'reactstrap';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

const LogoutContent = ({ titleTag: TitleTag }) => {
  useEffect(() => {
    async function onLoad() {
      localStorage.removeItem('bzAuthToken');
    }
    onLoad();
  }, []);

  return (
    <Fragment>
      {/* <img className="d-block mx-auto mb-4" src={rocket} alt="shield" width={70} /> */}
      <TitleTag>See you again!</TitleTag>
      <p>
        Thanks for using BugZero! You are <br className="d-none d-sm-block" />
        now successfully signed out.
      </p>
      <Button tag={Link} color="primary" size="sm" className="mt-3" to={`/authentication/login`}>
        <FontAwesomeIcon icon="chevron-left" transform="shrink-4 down-1" className="mr-1" />
        Return to Login
      </Button>
    </Fragment>
  );
};

LogoutContent.propTypes = {
  layout: PropTypes.string,
  titleTag: PropTypes.string
};

LogoutContent.defaultProps = {
  layout: 'basic',
  titleTag: 'h4'
};

export default LogoutContent;

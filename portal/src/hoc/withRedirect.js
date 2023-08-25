import React, { useState } from 'react';
import { Redirect } from 'react-router-dom';
import { aws } from '../config';

const withRedirect = OriginalComponent => {
  const UpdatedComponent = props => {
    // State
    const [redirect, setRedirect] = useState(false);
    const [redirectUrl, setRedirectUrl] = useState(aws.cognito.loginUrl);

    if (redirect) {
      console.log('redirect to', redirectUrl);
      window.location.href = redirectUrl;
      // return <Redirect to={redirectUrl} />;
    }

    return <OriginalComponent setRedirect={setRedirect} setRedirectUrl={setRedirectUrl} {...props} />;
  };

  return UpdatedComponent;
};

export default withRedirect;

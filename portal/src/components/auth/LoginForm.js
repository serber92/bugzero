import React, { useEffect } from 'react';
import { Button, Form, FormGroup } from 'reactstrap';
import { aws } from '../../config';
import { useLocation, useHistory } from 'react-router-dom';
import BZAPIService from '../../services/BZAPIService';
import SNAPIService from '../../services/SNAPIService';
import SETTINGS from '../../constants/settings';
import Loader from '../common/Loader';

const LoginForm = () => {
  const location = useLocation();
  let history = useHistory();
  const hasToken = location.hash && location.hash.indexOf('id_token=') !== -1;
  useEffect(() => {
    async function onLoad() {
      console.log('loading');
      console.log('location', location);
      // Detect if redirected from AWS Hosted login.
      if (location.hash && location.hash.indexOf('id_token=') !== -1) {
        // setIsLoading(true);
        const hash = location.hash.substr(1);
        const tokens = hash.split('&').reduce(function(res, item) {
          var parts = item.split('=');
          res[parts[0]] = parts[1];
          return res;
        }, {});
        console.log('tokens', tokens);
        const idToken = tokens.id_token;
        BZAPIService.apiClient.setHeader('Authorization', `Bearer ${idToken}`);
        localStorage.setItem('bzAuthToken', idToken);

        // Set baseURL for service if configured
        const serviceNowSettings = await BZAPIService.getSetting(SETTINGS.SERVICE_NOW);
        if (serviceNowSettings && serviceNowSettings.snAuthToken && serviceNowSettings.snApiUrl) {
          SNAPIService.apiClient.setHeader('Authorization', `Basic ${serviceNowSettings.snAuthToken}`);
          SNAPIService.apiClient.setBaseURL(serviceNowSettings.snApiUrl);
        }
        console.log('logged in', idToken);
        const redirect = localStorage.getItem('redirect');
        if (redirect) {
          localStorage.removeItem('redirect');
          window.location.pathname = redirect;
        } else history.push('/');
      }
    }

    onLoad();
  }, []);
  // Handler
  const handleSubmit = e => {
    e.preventDefault();
    console.log('aws.cognito.loginUrl', aws.cognito.loginUrl);
    window.location.href = aws.cognito.loginUrl;
  };

  return (
    <Form onSubmit={handleSubmit}>
      <FormGroup>
        {!hasToken ? (
          <Button color="primary" block className="mt-3">
            Log in
          </Button>
        ) : (
          <Loader />
        )}
      </FormGroup>
    </Form>
  );
};

export default LoginForm;

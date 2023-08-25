import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
// components
import Loading from '../components/Loading';
// libs
import { useAppContext } from '../libs/contextLib';
// services
import BZAPIService from '../services/BZAPIService';
// css
import './Login.css';

export default function Login() {
  const { userHasAuthenticated } = useAppContext();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function onLoad() {
      console.log('loading');
      console.log('location', location);
      // Detect if redirected from AWS Hosted login.
      if (location.hash && location.hash.indexOf('id_token=') !== -1) {
        setIsLoading(true);
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

        console.log('logged in', idToken);

        userHasAuthenticated(true);
        const redirect = localStorage.getItem('redirect');
        if (redirect) {
          localStorage.removeItem('redirect');
          window.location.pathname = redirect;
        }
      }
    }

    onLoad();
  }, []);

  return <div className="Login">{isLoading && <Loading />}</div>;
}

import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Layout from './layouts/Layout';
import SNAPIService from './services/SNAPIService';
import BZAPIService from './services/BZAPIService';
import SETTINGS from './constants/settings';

import 'react-toastify/dist/ReactToastify.min.css';
import 'react-datetime/css/react-datetime.css';
import 'react-image-lightbox/style.css';

const App = () => {
  useEffect(() => {
    onLoad();
  }, []);

  async function onLoad() {
    try {
      const bzAuthToken = localStorage.getItem('bzAuthToken');

      if (bzAuthToken) {
        BZAPIService.apiClient.setHeader('Authorization', `Bearer ${bzAuthToken}`);
        const serviceNowSettings = await BZAPIService.getSetting(SETTINGS.SERVICE_NOW);
        if (serviceNowSettings && serviceNowSettings.snAuthToken && serviceNowSettings.snApiUrl) {
          SNAPIService.apiClient.setHeader('Authorization', `Basic ${serviceNowSettings.snAuthToken}`);
          SNAPIService.apiClient.setBaseURL(serviceNowSettings.snApiUrl);
        }
      }
    } catch (e) {
      console.log(e);
    }
  }
  return (
    <Router basename={process.env.PUBLIC_URL}>
      <Layout />
    </Router>
  );
};

export default App;

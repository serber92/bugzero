#!/bin/bash
cd ../../

cd service-common/
npm i
sls deploy --stage freddiemac
cd ..
cd service-rest-api/
npm i
sls deploy --stage freddiemac
cd ..
cd service-vendor-cisco-callhome-api/
npm i serverless-python-requirements
sls deploy --stage freddiemac
cd ..
cd service-vendor-hpe-api/
npm i serverless-python-requirements
sls deploy --stage freddiemac
cd ..
cd service-vendor-rh-api/
npm i
sls deploy --stage freddiemac
cd ..
cd service-vendor-msft-api/
npm i serverless-python-requirements
sls deploy --stage freddiemac


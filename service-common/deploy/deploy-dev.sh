#!/bin/bash
cd ../../

cd service-common/
npm i
sls deploy --stage dev
cd ..
cd service-rest-api/
npm i
sls deploy --stage dev
cd ..
cd service-vendor-cisco-callhome-api/
npm i serverless-python-requirements
sls deploy --stage dev
cd ..
cd service-vendor-hpe-api/
npm i serverless-python-requirements
sls deploy --stage dev
cd ..
cd service-vendor-rh-api/
npm i
sls deploy --stage dev
cd ..
cd service-vendor-msft-api/
npm i serverless-python-requirements
sls deploy --stage dev
cd service-vendor-vmware-api/
npm i serverless-python-requirements
sls deploy --stage dev
cd service-vendor-mongodb-api/
npm i serverless-python-requirements
sls deploy --stage dev


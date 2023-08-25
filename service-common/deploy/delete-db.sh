#!/bin/bash
cd ../../

cd service-rest-api/
sls deploy --stage demo
cd ../service-vendor-cisco-callhome-api/
sls deploy --stage demo
cd ../service-vendor-hpe-api/
sls deploy --stage demo
cd ../service-vendor-rh-api/
sls deploy --stage demo
cd ../service-vendor-msft-api/
sls deploy --stage demo
# cd ../service-servicenow-api/
# sls deploy --stage demo
cd ../service-vendor-mongodb-api/
sls deploy --stage demo
cd ../service-vendor-vmware-api/
sls deploy --stage demo


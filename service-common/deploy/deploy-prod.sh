#!/bin/bash
export AWS_PROFILE=bz-app
cd ../services/

cd bug-event-processor/
sls deploy --stage prod
cd ..
cd bugzero-rest-api/
sls deploy --stage prod
cd ..
cd vendor-cisco-api/
sls deploy --stage prod
cd ..
cd vendor-hpe-api/
sls deploy --stage prod
cd ..
cd vendor-redhat-api/
sls deploy --stage prod
cd ..
cd managed-product-sync/
sls deploy --stage prod


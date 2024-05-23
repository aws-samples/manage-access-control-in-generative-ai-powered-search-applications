#!/bin/bash

export AWS_DEFAULT_REGION=us-west-2
CURRENT_DIR=$(pwd)

# Back to the current directory
cd $CURRENT_DIR

# Deploy OpenSearch Service
DOMAIN_NAME_PREFIX="aosdomain*"
# Check if the OpenSearch Service domain exists
if aws opensearch list-domain-names | grep -q "$DOMAIN_NAME_PREFIX"; then
    echo "OpenSearch Service domain $DOMAIN_NAME_PREFIX exists"
else
    echo "OpenSearch Service domain $DOMAIN_NAME_PREFIX does not exist"
    cdk deploy OpensearchCdkStack
    echo "Sleep around 15 minutes to wait for the OpenSearch Service domain to be created"
fi

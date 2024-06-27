#!/bin/bash

# Set the SSM parameter names
API_ENDPOINT_PARAM="APIGWInvokeEndpoint"
USER_POOL_ID_PARAM="UserPoolID"
USER_POOL_CLIENT_ID_PARAM="UserPoolClientID"

# Function to get parameter value from SSM
get_ssm_parameter() {
    aws ssm get-parameter --name "$1" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION
}

API_ENDPOINT=$(get_ssm_parameter $API_ENDPOINT_PARAM)
USER_POOL_ID=$(get_ssm_parameter $USER_POOL_ID_PARAM)
USER_POOL_CLIENT_ID=$(get_ssm_parameter $USER_POOL_CLIENT_ID_PARAM)

# Create or overwrite the .env.development file
cat << EOF > .env.development
VITE_REGION=$AWS_REGION
VITE_API_ENDPOINT=$API_ENDPOINT
VITE_USER_POOL_ID=$USER_POOL_ID
VITE_USER_POOL_CLIENT_ID=$USER_POOL_CLIENT_ID
EOF

echo ".env.development file has been created/updated with values from SSM Parameter Store."

#!/bin/bash

# Function to generate a complex password
generate_complex_password() {
    password=$(LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*()_+' < /dev/urandom | head -c 15)
    password="${password}2!"
    echo $password
}

# Get Cognito User Pool ID from SSM Parameter Store
USER_POOL_ID=$(aws ssm get-parameter --name "UserPoolID" --query "Parameter.Value" --output text)

if [ -z "$USER_POOL_ID" ]; then
    echo "Failed to retrieve Cognito User Pool ID from SSM Parameter Store"
    exit 1
fi

echo "Cognito User Pool ID: $USER_POOL_ID"

# File to store login information
OUTPUT_FILE="mock_users.txt"

# Clear the output file if it exists
> $OUTPUT_FILE

# Function to create a confirmed user
create_confirmed_user() {
    local custom_username=$1
    local email=$2
    local password=$3
    shift 3
    local attributes=("$@")

    # Create user
    aws cognito-idp admin-create-user \
        --user-pool-id $USER_POOL_ID \
        --username $custom_username \
        --user-attributes "${attributes[@]}" \
        --message-action SUPPRESS \
        --no-cli-pager

    # Set password and confirm user
    aws cognito-idp admin-set-user-password \
        --user-pool-id $USER_POOL_ID \
        --username $custom_username \
        --password "$password" \
        --permanent

    echo "$custom_username | $email | $password" >> $OUTPUT_FILE
}

# Create User 1
CUSTOM_USERNAME1="adminuser"
EMAIL1="adminuser@example.com"
PASSWORD1=$(generate_complex_password)
create_confirmed_user "$CUSTOM_USERNAME1" "$EMAIL1" "$PASSWORD1" \
    Name=email,Value=$EMAIL1 \
    Name=email_verified,Value=true \
    Name=custom:role,Value=admin \
    Name=custom:department,Value=engineering \
    Name=custom:access_level,Value=support

# Create User 2
CUSTOM_USERNAME2="engineer"
EMAIL2="engineer@example.com"
PASSWORD2=$(generate_complex_password)
create_confirmed_user "$CUSTOM_USERNAME2" "$EMAIL2" "$PASSWORD2" \
    Name=email,Value=$EMAIL2 \
    Name=email_verified,Value=true \
    Name=custom:role,Value=user \
    Name=custom:department,Value=engineering \
    Name=custom:access_level,Value=support

# Create User 3
CUSTOM_USERNAME3="researcher"
EMAIL3="researcher@example.com"
PASSWORD3=$(generate_complex_password)
create_confirmed_user "$CUSTOM_USERNAME3" "$EMAIL3" "$PASSWORD3" \
    Name=email,Value=$EMAIL3 \
    Name=email_verified,Value=true \
    Name=custom:role,Value=user \
    Name=custom:department,Value=research \
    Name=custom:access_level,Value=confidential

echo "Users created successfully. Login information saved to $OUTPUT_FILE"
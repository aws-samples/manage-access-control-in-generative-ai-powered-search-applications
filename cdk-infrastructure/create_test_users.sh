#!/bin/bash
export AWS_DEFAULT_REGION=us-east-1
CURRENT_DIR=$(pwd)

# Back to the current directory
cd $CURRENT_DIR

# Function to generate a complex password
generate_complex_password() {
    # Generate a 16-character password with at least one of each: uppercase, lowercase, number, and symbol
    password=$(LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*()_+' < /dev/urandom | head -c 15)
    password="${password}!"  # Ensure at least one symbol by appending an exclamation mark
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
OUTPUT_FILE="test_users_logins.txt"

# Clear the output file if it exists
> $OUTPUT_FILE

# Function to create a confirmed user
create_confirmed_user() {
    local username=$1
    local password=$2
    shift 2
    local attributes=("$@")

    # Create user
    aws cognito-idp admin-create-user \
        --user-pool-id $USER_POOL_ID \
        --username $username \
        --user-attributes "${attributes[@]}" \
        --message-action SUPPRESS

    # Set password and confirm user
    aws cognito-idp admin-set-user-password \
        --user-pool-id $USER_POOL_ID \
        --username $username \
        --password "$password" \
        --permanent

    echo "$username | $password" >> $OUTPUT_FILE
}

# Create User 1
USERNAME1="user1@example.com"
PASSWORD1=$(generate_complex_password)
create_confirmed_user "$USERNAME1" "$PASSWORD1" \
    Name=email,Value=$USERNAME1 \
    Name=email_verified,Value=true \
    Name=custom:role,Value=admin \
    Name=custom:department,Value=engineering \
    Name=custom:access_level,Value=support

# Create User 2
USERNAME2="user2@example.com"
PASSWORD2=$(generate_complex_password)
create_confirmed_user "$USERNAME2" "$PASSWORD2" \
    Name=email,Value=$USERNAME2 \
    Name=email_verified,Value=true \
    Name=custom:role,Value=user \
    Name=custom:department,Value=engineering \
    Name=custom:access_level,Value=support

# Create User 3
USERNAME3="user3@example.com"
PASSWORD3=$(generate_complex_password)
create_confirmed_user "$USERNAME3" "$PASSWORD3" \
    Name=email,Value=$USERNAME3 \
    Name=email_verified,Value=true \
    Name=custom:role,Value=user \
    Name=custom:department,Value=research \
    Name=custom:access_level,Value=confidential

echo "Users created successfully. Login information saved to $OUTPUT_FILE"
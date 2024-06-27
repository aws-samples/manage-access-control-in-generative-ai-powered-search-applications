#!/bin/bash

# Get the S3 bucket name from SSM Parameter Store
S3_BUCKET=$(aws ssm get-parameter --name "DataBucketName" --query "Parameter.Value" --output text)

if [ -z "$S3_BUCKET" ]; then
    echo "Failed to retrieve S3 bucket name from SSM Parameter Store"
    exit 1
fi

echo "S3 bucket to clean: $S3_BUCKET"

# Delete all objects within the S3 bucket
echo "Deleting all objects in the S3 bucket..."
aws s3 rm s3://$S3_BUCKET --recursive

# Execute CDK destroy command
echo "Executing CDK destroy..."
cdk destroy RAGCdkStack --force

echo "Cleanup completed successfully"
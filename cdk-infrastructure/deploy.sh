#!/bin/bash

export AWS_DEFAULT_REGION=us-east-1
CURRENT_DIR=$(pwd)

# Back to the current directory
cd $CURRENT_DIR
cdk deploy RAGCdkStack

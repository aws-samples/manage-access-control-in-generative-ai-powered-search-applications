STACK_NAME="fgac-frontend"
FRONTEND_REPOSITORY="https://github.com/ShinyTopology/test-rag-os-fgac"
SECRET_NAME_GITHUB_TOKEN=FrontendGithubToken

# Check if the stack exists
stack_exists=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].StackName" --output text 2>/dev/null)

if [ "$stack_exists" == "$STACK_NAME" ]; then
  echo "Stack $STACK_NAME exists. Deleting..."
  aws cloudformation delete-stack --stack-name $STACK_NAME
  echo "Stack $STACK_NAME deletion initiated."
else
  aws cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-body file://iac/frontend.yaml \
    --parameters ParameterKey=FrontendRepository,ParameterValue=$FRONTEND_REPOSITORY \
                 ParameterKey=GitHubTokenSecretName,ParameterValue=$SECRET_NAME_GITHUB_TOKEN \
    --capabilities CAPABILITY_NAMED_IAM
fi

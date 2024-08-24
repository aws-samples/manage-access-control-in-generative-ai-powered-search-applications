STACK_NAME="fgac-frontend"

# Check if the stack exists
stack_exists=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].StackName" --output text 2>/dev/null)

if [ "$stack_exists" == "$STACK_NAME" ]; then
  echo "Stack $STACK_NAME exists. Deleting..."
  aws cloudformation delete-stack --stack-name $STACK_NAME
  echo "Stack $STACK_NAME deletion initiated."
fi

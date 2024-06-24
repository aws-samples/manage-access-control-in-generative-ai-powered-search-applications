# Search Assisstant Lambda 
### Fn Input
- Environment variables:
    - AOS_ENDPOINT
    - USER_POOL_ID
    - AWS_REGION
    - AOS_INDEX
- API Gateway event (that includes the caller authorization token)

### Fn Output

{
    'statusCode': ...,
    'body': '<assisstant answer to the question>'
}
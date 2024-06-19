import os
from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_ssm as ssm,
    aws_cognito as cognito,
)

from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct

class RagCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        aos_endpoint = ssm.StringParameter.from_string_parameter_name(
            self, "ImportedAosEndpointParam",
            string_parameter_name="AosEndpoint"
        ).string_value

        aos_domain_arn = ssm.StringParameter.from_string_parameter_name(
            self, "ImportedAosArnParam",
            string_parameter_name="AosArn"
        ).string_value

        # Fetch Cognito User Pool ARN from SSM
        cognito_user_pool_arn = ssm.StringParameter.from_string_parameter_name(
            self, "ImportedCognitoUserPoolArn",
            string_parameter_name="CognitoUserPoolArn"
        ).string_value

        # Lambda Function for API Gateway
        invoke_model_lambda = PythonFunction(
            self, "InvokeModelLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            entry="rag_cdk/lambdas",
            index="invoke.py",
            handler="lambda_handler",
            memory_size=256,
            environment={
                "AOS_ENDPOINT": aos_endpoint,
                "INDEX_NAME": "test-index"
            },
            timeout=Duration.seconds(300),
        )

        # Add Bedrock permissions to the lambda function
        invoke_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"],
            effect=iam.Effect.ALLOW
        ))

        # Allow invoke_model_lambda to access OpenSearch on imported_aos_endpoint
        invoke_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "es:ESHttpGet",
                "es:ESHttpHead",
                "es:ESHttpPost"
            ],
            resources=[aos_domain_arn + "/*"],
            effect=iam.Effect.ALLOW
        ))

        # Allow access to Cognito
        invoke_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["cognito-idp:GetUser"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        ))

        # API Gateway REST API
        api = apigateway.RestApi(
            self,
            "RestApi",
            description="An API Gateway REST API and an AWS Lambda function.",
        )

        # Attach the lambda function to the REST API
        lambda_integration = apigateway.LambdaIntegration(invoke_model_lambda)

        # Create a Cognito user pool authorizer
        user_pool = cognito.UserPool.from_user_pool_arn(self, "ImportedUserPool", user_pool_arn=cognito_user_pool_arn)
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # Create a resource and method
        invoke_resource = api.root.add_resource("invoke")
        invoke_resource.add_method(
            "POST",
            lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )

        # Allow the lambda function to be invoked by the API Gateway
        invoke_model_lambda.add_permission(
            "InvokeModelLambdaPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*"
        )

        # Add API GW endpoint to parameter store
        ssm.StringParameter(self, "APIGWInvokeEndpoint",
            parameter_name="APIGWInvokeEndpoint",
            string_value=f"https://{api.rest_api_id}.execute-api.{Stack.of(self).region}.amazonaws.com/prod/invoke"
        )

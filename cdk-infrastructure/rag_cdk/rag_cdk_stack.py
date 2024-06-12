import os
from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigatewayv2,
    aws_ssm as ssm
)

from aws_cdk.aws_lambda_python_alpha import PythonFunction

from aws_cdk.aws_apigatewayv2_authorizers import WebSocketIamAuthorizer
from aws_cdk.aws_apigatewayv2_integrations import WebSocketLambdaIntegration
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


        # Lambda Functions for api gateway
        on_connect_lambda = _lambda.Function(
            self,
            "OnConnectLambdaFunction",
            code=_lambda.Code.from_asset("rag_cdk/lambdas"),
            handler="on_connect.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            memory_size=256,
            timeout=Duration.seconds(300)
        )

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

        
        
        # add Bedrock permissions to the lambda function
        invoke_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel", 
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"],
            effect=iam.Effect.ALLOW
        ))

        # allow invoke_model_lambda to access opensearch on imported_aos_endpoint
        invoke_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "es:ESHttpGet",
                "es:ESHttpHead",
                "es:ESHttpPost"
            ],
            resources=[aos_domain_arn + "/*"],
            effect=iam.Effect.ALLOW
        ))

        on_disconnect_lambda = _lambda.Function(
            self,
            "OnDisconnectLambdaFunction",
            code=_lambda.Code.from_asset("rag_cdk/lambdas"),
            handler="onDisconnect.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            memory_size=256,
            timeout=Duration.seconds(300)
        )
            
        # API Gateway WebSocket API
        api = apigatewayv2.WebSocketApi(
            self,
            "WebSocketApi",
            description="An Amazon API Gateway WebSocket API and an AWS Lambda function.",
            # route_selection_expression="$request.body.action",
            connect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration("ConnectIntegration", on_connect_lambda),
                authorizer=WebSocketIamAuthorizer()
            ),
            disconnect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration("DisconnectIntegration", on_disconnect_lambda)
            ),
            default_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration("DefaultIntegration", invoke_model_lambda)
            )
        )

        invoke_model_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["execute-api:ManageConnections"],
            resources=[f"arn:aws:execute-api:{self.region}:{self.account}:{api.api_id}/*/@connections/*"],
        ))

        # allow lambdas to be invoked by the api, use map to assign permissions to all lambdas
        for lambda_func in [on_connect_lambda, invoke_model_lambda, on_disconnect_lambda]:
            lambda_func.add_permission(
                "InvokeModelLambdaPermission",
                principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
                source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.api_id}/*",
            )

        api_stage = apigatewayv2.WebSocketStage(self, "DevStage",
            web_socket_api=api,
            stage_name="dev",
            auto_deploy=True
        )

        # Add API GW endpoint to parameter store
        ssm.StringParameter(self, "APIGWInvokeEndpoint",
            parameter_name="APIGWInvokeEndpoint",
            string_value=f"wss://{api.api_id}.execute-api.{Stack.of(self).region}.amazonaws.com/{api_stage.stage_name}"
        )



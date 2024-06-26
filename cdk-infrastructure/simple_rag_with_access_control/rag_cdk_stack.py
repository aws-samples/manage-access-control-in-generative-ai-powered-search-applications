import json
from aws_cdk import (
    Stack,
    aws_opensearchservice as aos,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_deployment as s3deploy,
    aws_apigateway as apigateway,
    RemovalPolicy,
    Duration,
)
from constructs import Construct
from aws_cdk.aws_lambda_python_alpha import PythonFunction


class RAGCdkStack(Stack):

    def add_to_param_store(self, id: str, name: str, value: str) -> None:
        ssm.StringParameter(self, id, parameter_name=name, string_value=value)

    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create OpenSearch domain
        prod_domain = aos.Domain(
            self,
            "AosDomain",
            version=aos.EngineVersion.OPENSEARCH_2_11,
            node_to_node_encryption=True,
            encryption_at_rest=aos.EncryptionAtRestOptions(enabled=True),
            enforce_https=True,
            capacity=aos.CapacityConfig(
                data_node_instance_type="m5.xlarge.search",
                data_nodes=2,
                multi_az_with_standby_enabled=False,
            ),
            ebs=aos.EbsOptions(volume_size=20),
            zone_awareness=aos.ZoneAwarenessConfig(enabled=False),
            logging=aos.LoggingOptions(
                slow_search_log_enabled=True,
                app_log_enabled=True,
                slow_index_log_enabled=True,
            ),
        )

        # Add Cognito user pool
        user_pool = cognito.UserPool(
            self,
            "AOSUserPool",
            custom_attributes={
                "department": cognito.StringAttribute(
                    min_len=1, max_len=100, mutable=True
                ),
                "access_level": cognito.StringAttribute(
                    min_len=1, max_len=100, mutable=True
                ),
                "role": cognito.StringAttribute(
                    min_len=1, max_len=100, mutable=True
                ),
            },
        )
        user_pool_client = cognito.UserPoolClient(
            self,
            "AOSClient",
            user_pool=user_pool,
            auth_flows={
                "user_password": True,
            },
        )
        user_pool_domain = cognito.UserPoolDomain(
            self,
            "Domain",
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=config["COGNITO_DOMAIN_PREFIX"]
            ),
        )

        # Add S3 bucket data
        data_bucket = s3.Bucket(
            self, "S3BucketForDataIngestion", removal_policy=RemovalPolicy.DESTROY
        )

        bucket_deployment = s3deploy.BucketDeployment(
            self,
            "DeployJson",
            sources=[s3deploy.Source.asset("./simple_rag_with_access_control/data")],
            destination_bucket=data_bucket,
        )

        # Add Ingestion Lambda
        ingestion_lambda_function = PythonFunction(
            self,
            "DataIngestionLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            entry="simple_rag_with_access_control/lambda/ingestion",
            handler="handler",
            timeout=Duration.seconds(900),
            memory_size=512,
            environment={
                "BUCKET_NAME": data_bucket.bucket_name,
                "AOS_ENDPOINT": prod_domain.domain_endpoint,
            },
        )
        ingestion_lambda_function.role.attach_inline_policy(
            iam.Policy(
                self,
                "IngestionLambdaExecutionPolicy",
                statements=[
                    iam.PolicyStatement(
                        actions=["s3:GetObject"],
                        resources=[data_bucket.bucket_arn + "/*"],
                        effect=iam.Effect.ALLOW,
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "es:ESHttpPost",
                            "es:ESHttpPut",
                            "es:ESHttpGet",
                            "es:ESHttpDelete",
                        ],
                        resources=[prod_domain.domain_arn + "/*"],
                        effect=iam.Effect.ALLOW,
                    ),
                    iam.PolicyStatement(
                        actions=["bedrock:InvokeModel"],
                        resources=["*"],
                        effect=iam.Effect.ALLOW,
                    ),
                ],
            )
        )

        # Lambda Function for API Gateway
        search_lambda = PythonFunction(
            self,
            "SearchLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            entry="simple_rag_with_access_control/lambda/search",
            handler="handler",
            memory_size=512,
            environment={
                "AOS_ENDPOINT": prod_domain.domain_endpoint,
                "AOS_INDEX": "test-index",
            },
            timeout=Duration.seconds(300),
        )

        search_lambda.role.attach_inline_policy(
            iam.Policy(
                self,
                "SearchLambdaExecutionPolicy",
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                        ],
                        resources=["*"],
                        effect=iam.Effect.ALLOW,
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "es:ESHttpPost",
                            "es:ESHttpPut",
                            "es:ESHttpGet",
                            "es:ESHttpDelete",
                        ],
                        resources=[prod_domain.domain_arn + "/*"],
                        effect=iam.Effect.ALLOW,
                    ),
                    iam.PolicyStatement(
                        actions=["cognito-idp:GetUser"],
                        resources=[f"{user_pool.user_pool_arn}/*"],
                        effect=iam.Effect.ALLOW,
                    ),
                ],
            )
        )

        # Lambda Function for API Gateway
        access_modifier_lambda = PythonFunction(
            self,
            "AccessModifierLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            entry="simple_rag_with_access_control/lambda/access_modifier",
            handler="handler",
            memory_size=512,
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
            },
            timeout=Duration.seconds(300),
        )


        access_modifier_lambda.role.attach_inline_policy(
            iam.Policy(
                self,
                "AccessModifierLambdaExecutionPolicy",
                statements=[
                    iam.PolicyStatement(
                        actions=["cognito-idp:AdminUpdateUserAttributes"],
                        resources=[user_pool.user_pool_arn],
                        effect=iam.Effect.ALLOW,
                    ),
                ],
            )
        )


        # API Gateway REST API
        api = apigateway.RestApi(
            self,
            "RestApi",
            description="An API Gateway REST API and an AWS Lambda function.",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )

        # Attach the lambda function to the REST API
        search_lambda_integration = apigateway.LambdaIntegration(search_lambda)
        access_modifier_lambda_integration = apigateway.LambdaIntegration(access_modifier_lambda)


        # Create a Cognito user pool authorizer
        user_pool = cognito.UserPool.from_user_pool_arn(
            self, "ImportedUserPool", user_pool_arn=user_pool.user_pool_arn
        )
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer", cognito_user_pools=[user_pool]
        )

        # Create a resource and method
        invoke_resource = api.root.add_resource("invoke")
        invoke_resource.add_method(
            "POST",
            search_lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # Allow the lambda function to be invoked by the API Gateway
        search_lambda.add_permission(
            "InvokeModelLambdaPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*",
        )

        access_resource = api.root.add_resource("access")
        access_resource.add_method(
            "POST",
            access_modifier_lambda_integration,
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # Allow the lambda function to be invoked by the API Gateway
        access_modifier_lambda.add_permission(
            "InvokeModelLambdaPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*",
        )

        # Add OpenSearch domain level access policy
        prod_domain.add_access_policies(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ArnPrincipal(ingestion_lambda_function.role.role_arn),
                    iam.ArnPrincipal(search_lambda.role.role_arn),
                ],
                actions=["es:ESHttp*"],
                resources=[f"{prod_domain.domain_arn}/*"],
            )
        )
        
        self.add_to_param_store(
            "AosEndpointParam", "AosEndpoint", prod_domain.domain_endpoint
        )
        self.add_to_param_store("AosArnParam", "AosArn", prod_domain.domain_arn)
        self.add_to_param_store(
            "UserPoolArn", "CognitoUserPoolArn", user_pool.user_pool_arn
        )

        self.add_to_param_store(
            "UserPoolClientID", "UserPoolClientID", user_pool_client.user_pool_client_id
        )
        self.add_to_param_store(
            "UserPoolID", "UserPoolID", user_pool.user_pool_id
        )
        self.add_to_param_store(
            "DataBucketName", "DataBucketName", data_bucket.bucket_name
        )
        self.add_to_param_store(
            "APIGWInvokeEndpoint",
            "APIGWInvokeEndpoint",
            f"https://{api.rest_api_id}.execute-api.{Stack.of(self).region}.amazonaws.com/prod/invoke",
        )
        self.add_to_param_store(
            "APIGWModifyAttributesEndpoint",
            "APIGWModifyAttributesEndpoint",
            f"https://{api.rest_api_id}.execute-api.{Stack.of(self).region}.amazonaws.com/prod/access",
        )
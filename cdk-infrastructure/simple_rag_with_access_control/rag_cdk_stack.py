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
from typing import Tuple, Dict


class RAGCdkStack(Stack):

    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create OpenSearch domain
        prod_domain = self.create_opensearch_domain()

        # Create Cognito user pool and client
        user_pool, user_pool_client = self.create_cognito_user_pool(config)

        # Add S3 bucket for data
        data_bucket = self.create_s3_bucket()

        # Deploy data to S3 bucket
        self.deploy_data_to_s3_bucket(data_bucket)

        # Add Lambda functions
        ingestion_lambda_function = self.create_lambda_function(
            "DataIngestionLambda",
            "simple_rag_with_access_control/lambda/ingestion",
            {
                "BUCKET_NAME": data_bucket.bucket_name,
                "AOS_ENDPOINT": prod_domain.domain_endpoint,
            },
            self.get_ingestion_lambda_policy(data_bucket, prod_domain),
        )

        search_lambda = self.create_lambda_function(
            "SearchLambdaFunction",
            "simple_rag_with_access_control/lambda/search",
            {"AOS_ENDPOINT": prod_domain.domain_endpoint, "AOS_INDEX": "test-index"},
            self.get_search_lambda_policy(user_pool, prod_domain),
        )

        access_modifier_lambda = self.create_lambda_function(
            "AccessModifierLambdaFunction",
            "simple_rag_with_access_control/lambda/access_modifier",
            {"USER_POOL_ID": user_pool.user_pool_id},
            self.get_access_modifier_lambda_policy(user_pool),
        )

        # Create API Gateway and endpoints
        api = self.create_api_gateway()
        self.create_api_methods(api, search_lambda, access_modifier_lambda, user_pool)

        # Add OpenSearch domain access policies
        self.add_opensearch_access_policies(
            prod_domain, ingestion_lambda_function, search_lambda
        )

        # Store parameters in SSM
        self.store_parameters_in_ssm(
            prod_domain, user_pool, user_pool_client, data_bucket, api
        )

    def add_to_param_store(self, id: str, name: str, value: str) -> None:
        ssm.StringParameter(self, id, parameter_name=name, string_value=value)

    def create_opensearch_domain(self) -> aos.Domain:
        return aos.Domain(
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
            removal_policy=RemovalPolicy.DESTROY,
        )

    def create_cognito_user_pool(
        self, config: dict
    ) -> Tuple[cognito.UserPool, cognito.UserPoolClient]:
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
                "role": cognito.StringAttribute(min_len=1, max_len=100, mutable=True),
            },
            removal_policy=RemovalPolicy.DESTROY,
        )
        user_pool_client = cognito.UserPoolClient(
            self,
            "AOSClient",
            user_pool=user_pool,
            auth_flows={"user_password": True, "user_srp": True},
        )
        cognito.UserPoolDomain(
            self,
            "Domain",
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=config["COGNITO_DOMAIN_PREFIX"]
            ),
        )
        return user_pool, user_pool_client

    def create_s3_bucket(self) -> s3.Bucket:
        return s3.Bucket(
            self, "S3BucketForDataIngestion", removal_policy=RemovalPolicy.DESTROY
        )

    def deploy_data_to_s3_bucket(self, bucket: s3.Bucket) -> None:
        s3deploy.BucketDeployment(
            self,
            "DeployJson",
            sources=[s3deploy.Source.asset("./simple_rag_with_access_control/data")],
            destination_bucket=bucket,
        )

    def create_lambda_function(
        self, id: str, entry: str, environment: Dict[str, str], policy: iam.Policy
    ) -> PythonFunction:
        lambda_function = PythonFunction(
            self,
            id,
            runtime=_lambda.Runtime.PYTHON_3_11,
            entry=entry,
            handler="handler",
            timeout=Duration.seconds(900),
            memory_size=512,
            environment=environment,
        )
        lambda_function.role.attach_inline_policy(policy)
        return lambda_function

    def get_ingestion_lambda_policy(
        self, bucket: s3.Bucket, domain: aos.Domain
    ) -> iam.Policy:
        return iam.Policy(
            self,
            "IngestionLambdaExecutionPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[bucket.bucket_arn + "/*"],
                    effect=iam.Effect.ALLOW,
                ),
                iam.PolicyStatement(
                    actions=[
                        "es:ESHttpPost",
                        "es:ESHttpPut",
                        "es:ESHttpGet",
                        "es:ESHttpDelete",
                    ],
                    resources=[domain.domain_arn + "/*"],
                    effect=iam.Effect.ALLOW,
                ),
                iam.PolicyStatement(
                    actions=["bedrock:InvokeModel"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW,
                ),
            ],
        )

    def get_search_lambda_policy(
        self, user_pool: cognito.UserPool, domain: aos.Domain
    ) -> iam.Policy:
        return iam.Policy(
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
                    resources=[domain.domain_arn + "/*"],
                    effect=iam.Effect.ALLOW,
                ),
                iam.PolicyStatement(
                    actions=["cognito-idp:GetUser"],
                    resources=[f"{user_pool.user_pool_arn}/*"],
                    effect=iam.Effect.ALLOW,
                ),
            ],
        )

    def get_access_modifier_lambda_policy(
        self, user_pool: cognito.UserPool
    ) -> iam.Policy:
        return iam.Policy(
            self,
            "AccessModifierLambdaExecutionPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "cognito-idp:AdminUpdateUserAttributes",
                        "cognito-idp:ListUsers",
                    ],
                    resources=[user_pool.user_pool_arn, f"{user_pool.user_pool_arn}/*"],
                    effect=iam.Effect.ALLOW,
                ),
            ],
        )

    def create_api_gateway(self) -> apigateway.RestApi:
        return apigateway.RestApi(
            self,
            "RestApi",
            description="An API Gateway REST API and an AWS Lambda function.",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )

    def create_api_methods(
        self,
        api: apigateway.RestApi,
        search_lambda: PythonFunction,
        access_modifier_lambda: PythonFunction,
        user_pool: cognito.UserPool,
    ) -> None:

        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer", cognito_user_pools=[user_pool]
        )

        self.add_api_method(
            api, "invoke", ["POST"], search_lambda, authorizer
        )
        self.add_api_method(
            api,
            "access",
            ["POST", "GET"],
            access_modifier_lambda,
            authorizer,
        )

    def add_api_method(
        self,
        api: apigateway.RestApi,
        method_name: str,
        http_methods: list[str],
        lambda_function: PythonFunction,
        authorizer: apigateway.CognitoUserPoolsAuthorizer,
    ) -> None:
        resource = api.root.add_resource(method_name)
        integration = apigateway.LambdaIntegration(lambda_function)
        for method in http_methods:
            resource.add_method(
                method,
                integration,
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
        lambda_function.add_permission(
            f"InvokePermission{method}",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*",
        )

    def add_opensearch_access_policies(
        self,
        domain: aos.Domain,
        ingestion_lambda: PythonFunction,
        search_lambda: PythonFunction,
    ) -> None:
        domain.add_access_policies(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ArnPrincipal(ingestion_lambda.role.role_arn),
                    iam.ArnPrincipal(search_lambda.role.role_arn),
                ],
                actions=["es:ESHttp*"],
                resources=[f"{domain.domain_arn}/*"],
            )
        )

    def store_parameters_in_ssm(
        self,
        domain: aos.Domain,
        user_pool: cognito.UserPool,
        user_pool_client: cognito.UserPoolClient,
        bucket: s3.Bucket,
        api: apigateway.RestApi,
    ) -> None:
        self.add_to_param_store(
            "AosEndpointParam", "AosEndpoint", domain.domain_endpoint
        )
        self.add_to_param_store("AosArnParam", "AosArn", domain.domain_arn)
        self.add_to_param_store(
            "UserPoolArn", "CognitoUserPoolArn", user_pool.user_pool_arn
        )
        self.add_to_param_store(
            "UserPoolClientID", "UserPoolClientID", user_pool_client.user_pool_client_id
        )
        self.add_to_param_store("UserPoolID", "UserPoolID", user_pool.user_pool_id)
        self.add_to_param_store("DataBucketName", "DataBucketName", bucket.bucket_name)
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

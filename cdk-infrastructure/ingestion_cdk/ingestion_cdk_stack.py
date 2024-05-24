import json
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_ssm as ssm,
    RemovalPolicy,
    Duration
    )
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct

class IngestionCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        aos_endpoint_param = ssm.StringParameter.from_string_parameter_attributes(
            self,
            "AosEndpointParam",
            parameter_name="AosEndpoint",
            simple_name=True,
        )

        aos_endpoint = aos_endpoint_param.string_value

        # Define the S3 bucket for the OpenSearch deployment
        data_bucket = s3.Bucket(self, "S3BucketForDataIngestion",
            removal_policy=RemovalPolicy.DESTROY
        )

        #upload aims.json to the S3 bucket from folder aims_opensearch_cdk/custom_resources/data
        bucket_deployment = s3deploy.BucketDeployment(self, "DeployAimsJson",
            sources=[s3deploy.Source.asset("./ingestion_cdk/data", exclude=["*", "!*.json"])],
            destination_bucket=data_bucket,
        )

        # Define the Lambda function for the OpenSearch deployment
        on_create_lambda_function = PythonFunction(self, "DataIngestionLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            entry="ingestion_cdk/ingestion_lambda",
            handler="handler",
            timeout=Duration.seconds(180),
            environment={
                "BUCKET_NAME": data_bucket.bucket_name,
                "AOS_ENDPOINT": aos_endpoint
            }
        )

        # IAM policy for Lambda function
        on_create_lambda_function.role.attach_inline_policy(iam.Policy(self, "LambdaExecutionPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[data_bucket.bucket_arn + "/*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["es:ESHttpPost", "es:ESHttpPut", "es:ESHttpGet", "es:ESHttpDelete"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["bedrock:InvokeModel"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),

            ]
        ))

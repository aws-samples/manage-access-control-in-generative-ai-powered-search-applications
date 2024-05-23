import json
from aws_cdk import (
    Stack,
    aws_opensearchservice as aos,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_cognito_identitypool_alpha as identitypool_alpha,
    aws_ssm as ssm,
    )
from constructs import Construct

class OpensearchCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_pool = cognito.UserPool(self, 'AOSUserPool')

        user_pool_client = cognito.UserPoolClient(self, 'AOSClient',
            user_pool=user_pool,
            generate_secret=True,
            auth_flows={
                "user_password": True,
            }
        )

        identity_pool = identitypool_alpha.IdentityPool(self, 
            "AOSIdentityPool",
            authentication_providers=identitypool_alpha.IdentityPoolAuthenticationProviders(
                user_pools=[
                    identitypool_alpha.UserPoolAuthenticationProvider(
                        user_pool_client=user_pool_client,
                        user_pool=user_pool
                    )
                ]
            ),
            allow_unauthenticated_identities=False
        )

        user_pool_domain = cognito.UserPoolDomain(self, 'Domain',
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=config['OPENSEARCH_COGNITO_DOMAIN_PREFIX']
            )
        )

        prod_domain = aos.Domain(self, "AosDomain",
            version=aos.EngineVersion.OPENSEARCH_2_11,
            node_to_node_encryption=True,
            encryption_at_rest=aos.EncryptionAtRestOptions(
                enabled=True
            ),
            enforce_https=True,
            cognito_dashboards_auth=aos.CognitoOptions(
                identity_pool_id=identity_pool.identity_pool_id,
                user_pool_id=user_pool.user_pool_id,
                role=iam.Role(
                    self, "CognitoAccessRole",
                    assumed_by=iam.ServicePrincipal("opensearchservice.amazonaws.com"),
                    managed_policies=[
                        iam.ManagedPolicy.from_aws_managed_policy_name("AmazonOpenSearchServiceCognitoAccess")
                    ]
                )
            ),
            capacity=aos.CapacityConfig(
                #master_nodes=1,
                data_node_instance_type="m5.xlarge.search",
                data_nodes=1,
                multi_az_with_standby_enabled=False
            ),
            ebs=aos.EbsOptions(
                volume_size=20
            ),
            zone_awareness=aos.ZoneAwarenessConfig(
                #availability_zone_count=1,
                enabled=False
            ),
            logging=aos.LoggingOptions(
                slow_search_log_enabled=True,
                app_log_enabled=True,
                slow_index_log_enabled=True
            )
        )

        prod_domain.add_access_policies(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ArnPrincipal(identity_pool.authenticated_role.role_arn),
                ],
                actions=[
                    "es:ESHttp*"
                ],
                resources=[
                    f"{prod_domain.domain_arn}/*"
                ]
            )
        )

        # add permissions to identity_pool's authenticated role
        authenticated_role_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["es:ESHttp*"],
            resources=[f"{prod_domain.domain_arn}/*"]
        )

        identity_pool.authenticated_role.add_to_principal_policy(authenticated_role_policy)


        # Crate an SSM parameter for AOSEndpoint
        ssm.StringParameter(self, "AosEndpointParam",
            parameter_name="AosEndpoint",
            string_value=prod_domain.domain_endpoint
        )

        # Crate an SSM parameter for AOS ARN
        ssm.StringParameter(self, "AosArnParam",
            parameter_name="AosArn",
            string_value=prod_domain.domain_arn
        )

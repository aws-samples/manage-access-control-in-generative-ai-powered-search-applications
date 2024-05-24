#!/usr/bin/env python3
import os

import aws_cdk as cdk

from  opensearch_cdk.opensearch_cdk_stack import OpensearchCdkStack
from ingestion_cdk.ingestion_cdk_stack import IngestionCdkStack

def load_env_config(file_name):
    """Load configuration variables from a file."""
    config = {}
    with open(file_name) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config


env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"]
)

config = load_env_config('prod.env')

app = cdk.App()
OpensearchCdkStack(app, "OpensearchCdkStack", config=config)
IngestionCdkStack(app, "IngestionCdkStack", config=config)

app.synth()

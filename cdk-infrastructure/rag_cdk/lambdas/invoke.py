
import boto3
import json
import os
import logging
from botocore.exceptions import ClientError

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

# initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ENV variables
region = os.environ["AWS_REGION"]
domain_endpoint = os.environ['AOS_ENDPOINT']
index_name = os.environ['INDEX_NAME']

def initialize_opensearch_client():
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, "es")
    os_client = OpenSearch(
        hosts=[{'host': domain_endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20
    )

    # Test connection
    try:
        response = os_client.info()
        logger.warning(f"Connection to OpenSearch successful. Cluster name: {response['cluster_name']}")
        return os_client
    except Exception as e:
        logger.error(f"Connection to OpenSearch failed {domain_endpoint}. Detailed error: {str(e)}")


def lambda_handler(event, context):
    print("Event: ", json.dumps(event))

    # Handle preflight (OPTIONS) request
    if event['httpMethod'] == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": ""
        }

    # Extract information from event
    # TODO: add RAG logic

    sample_response = {
        "type": "ai",
        "content": "Some answers here",
    }


    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(sample_response)
    }

    return response
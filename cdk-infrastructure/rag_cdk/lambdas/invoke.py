
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

    # handle websockets request
    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")
    if route_key is None or connection_id is None:
        return {"statusCode": 400}

    logger.info("Request: %s", route_key)

    # set default status code
    response = {"statusCode": 200}

    # extract information from event
    body = json.loads(event.get("body"))
    domain = event.get("requestContext", {}).get("domainName")
    stage = event.get("requestContext", {}).get("stage")
    query = body["query"]

    # TODO add RAG logic
    return "200"
import json
import boto3
import os
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 client initialization
s3_client = boto3.client('s3')

# # Environment variables
bucket_name = os.environ['BUCKET_NAME']
region = os.environ['AWS_REGION']
domain_endpoint = os.environ["AOS_ENDPOINT"]
index_name = None

# Helper function to load JSON from S3
def load_json_from_s3(filename: str) -> dict:
    file = s3_client.get_object(Bucket=bucket_name, Key=filename)
    return json.loads(file['Body'].read().decode('utf-8'))


def create_os_client() -> OpenSearch:
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, "es")
    return OpenSearch(
        hosts=[{'host': domain_endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize = 20
    )

def generate_embdeddings(model_provider: str, model_id: str, doc_text: str) -> list[float]:
    if model_provider == "bedrock":
        bedrock_runtime = boto3.client("bedrock-runtime", region_name = region)
        body = json.dumps({"texts": [doc_text],"input_type":"search_document"})
        response = bedrock_runtime.invoke_model(
            body=body, modelId=model_id, accept="*/*", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embeddings")[0]
    
        print(f"The embedding vector has {len(embedding)} values\n{embedding[0:3]+['...']+embedding[-3:]}")
    
    else:
        raise ValueError(f"Model provider {model_provider} is not supported.")

    return embedding


def format_bulk_data_for_os_input(bulk_data: list[dict], index_name: str, model_id: str, model_provider: str) -> list[dict]:
    formatted_bulk_data = []
    for doc in bulk_data:
        doc["doc_embedding"] = generate_embdeddings(model_provider, model_id, doc['doc_text'])
        formatted_bulk_data.append({"index": {"_index": index_name, "_id": doc["doc_id"]}})
        formatted_bulk_data.append(doc)
    return formatted_bulk_data


def handler(event, context):
    print(event)

    create_index = event.get('create_index', False)
    model_provider = event.get('model_provider', 'bedrock')
    model_id = event.get('model_id', 'cohere.embed-multilingual-v3')
    if create_index:
        index_file_s3_path = event.get('index_file_s3_path')
        mappings_file_s3_path = event.get('mappings_file_s3_path')

    load_data = event.get('load_data', False)
    if load_data:
        data_file_s3_path = event.get('data_file_s3_path')

    index_name = event.get('index_name', 'test-index')

    # OpenSearch client initialization
    os_client = create_os_client()

    # Test connection
    response = os_client.info()
    logger.warning(f"Connection to OpenSearch successful. Cluster name: {response['cluster_name']}")

    if create_index:
        # Creating index with settings and mappings
        index_body = {
            'settings': load_json_from_s3(index_file_s3_path),
            'mappings': load_json_from_s3(mappings_file_s3_path)
        }

        # Create index and mappings
        try:
            os_client.indices.create(index=index_name, body=index_body)
            logger.info(f"Index {index_name} created successfully.")
        except Exception as e:
            if 'resource_already_exists_exception' in str(e):
                logger.warning(f"WARNING: Index {index_name} already exists.")
            else:
                logger.error(f"Failed to create index {index_name}. Detailed error: {str(e)}")
                raise e
    else:
        logger.info("No index creation requested.")
    
    if load_data:
        # Perform bulk upload to OpenSearch
        try:
            bulk_data = load_json_from_s3(data_file_s3_path)
            formatted_bulk_data = format_bulk_data_for_os_input(bulk_data, index_name, model_id, model_provider)
            response = os_client.bulk(body=formatted_bulk_data)
            logger.warning("Bulk upload completed.")
        except Exception as e:
            logger.error(f"Failed to upload data to OpenSearch. Detailed error: {str(e)}")
            raise e
        
        # Query OpenSearch to verify bulk upload
        query_body = {"query": {"match_all": {}}}
        response = os_client.search(index=index_name, body=query_body)
        logger.info(f"Total records in index {index_name}: {response['hits']['total']['value']}")
        logger.info(f"Partial response [:5]: {response['hits']['hits'][:5]}")
    else:
        logger.info("No data loading requested.")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda execution and data loading completed successfully.')
    }

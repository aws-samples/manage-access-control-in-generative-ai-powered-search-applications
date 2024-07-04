import json
import logging
import os
import zipfile

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 client initialization
s3_client = boto3.client("s3")

# # Environment variables
bucket_name = os.environ["BUCKET_NAME"]
region = os.environ["AWS_REGION"]
domain_endpoint = os.environ["AOS_ENDPOINT"]
custom_attributes = os.environ["CUSTOM_ATTRIBUTES"]


# Helper function to load JSON from S3
def load_json_from_s3(filename: str) -> dict:
    file = s3_client.get_object(Bucket=bucket_name, Key=filename)
    return json.loads(file["Body"].read().decode("utf-8"))


def add_extra_mapping_attributes(mappings: dict) -> dict:
    for attr in custom_attributes.split(","):
        mappings["properties"][attr] = {
            "type": "text"
        }
    return mappings

def create_os_client() -> OpenSearch:
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, "es")
    return OpenSearch(
        hosts=[{"host": domain_endpoint, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,
    )


def generate_embdeddings(
    model_provider: str, model_id: str, doc_text: str
) -> list[float]:
    if model_provider == "bedrock":
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        body = json.dumps({"inputText": doc_text, "dimensions": 1024})
        response = bedrock_runtime.invoke_model(
            body=body, modelId=model_id, accept="*/*", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embedding")

    else:
        raise ValueError(f"Model provider {model_provider} is not supported.")

    return embedding


def bulk_data_upload_to_os(
    data_file_name: str,
    directory: str,
    index_name: str,
    model_id: str,
    model_provider: str,
    os_client: boto3.client
) -> list[dict]:
    formatted_bulk_data = []
    directory = f"/tmp/{data_file_name.split('.')[0]}/{directory}"
    print(directory)
    print(os.listdir("/tmp/")) 
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            doc = {}
            # Construct the full file path
            file_path = os.path.join(directory, filename)

            # Open the file and read its contents
            with open(file_path, "r") as file:
                file_contents = file.read()

            doc["doc_embedding"] = generate_embdeddings(
                model_provider, model_id, file_contents
            )
            doc["doc_text"] = file_contents

            # Read metadata from associated JSON file
            json_filename = os.path.splitext(filename)[0] + '.json'
            json_file_path = os.path.join(directory, json_filename)
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r') as json_file:
                    metadata = json.load(json_file)
                    doc.update(metadata)
            else:
                logger.warning(f"No metadata file found for {filename}")

            formatted_bulk_data.append(
                {"index": {"_index": index_name, "_id": filename}}
            )

            formatted_bulk_data.append(doc)
        if len(formatted_bulk_data) == 400: # bulk upload 400 documents at a time
            os_client.bulk(body=formatted_bulk_data)
            print("Successfully uploaded a bulk document")
            formatted_bulk_data = []

    os_client.bulk(body=formatted_bulk_data)



def download_docs(file_name: str):

    # Download the file from S3
    local_file_path = "/tmp/" + file_name
    s3_client.download_file(bucket_name, file_name, local_file_path)

    # Unzip the downloaded file
    with zipfile.ZipFile(local_file_path, "r") as zip_ref:
        zip_ref.extractall("/tmp/")

    print(f"File '{file_name}' downloaded and unzipped successfully.")


def handler(event, context):
    print(event)
    data_file_name = event["data_file_s3_path"]
    download_docs(data_file_name)

    create_index = event.get("create_index", False)
    model_provider = event.get("model_provider", "bedrock")
    model_id = event.get("model_id", "amazon.titan-embed-text-v2:0")
    load_data = event.get("load_data", True)

    if create_index:
        index_file_s3_path = event.get("index_file_s3_path")
        mappings_file_s3_path = event.get("mappings_file_s3_path")

    index_name = event.get("index_name", "test-index")

    # OpenSearch client initialization
    os_client = create_os_client()

    # Test connection
    response = os_client.info()
    logger.warning(
        f"Connection to OpenSearch successful. Cluster name: {response['cluster_name']}"
    )

    if create_index:
        # Creating index with settings and mappings
        mappings = load_json_from_s3(mappings_file_s3_path)
        mappings = add_extra_mapping_attributes(mappings)
        index_body = {
            "settings": load_json_from_s3(index_file_s3_path),
            "mappings": mappings,
        }

        # Create index and mappings
        try:
            os_client.indices.create(index=index_name, body=index_body)
            logger.info(f"Index {index_name} created successfully.")
        except Exception as e:
            if "resource_already_exists_exception" in str(e):
                logger.warning(f"WARNING: Index {index_name} already exists.")
            else:
                logger.error(
                    f"Failed to create index {index_name}. Detailed error: {str(e)}"
                )
                raise e
    else:
        logger.info("No index creation requested.")

    if load_data:
        # Perform bulk upload to OpenSearch
        bulk_data_upload_to_os(
            data_file_name=data_file_name,
            directory="data",
            index_name=index_name,
            model_id=model_id,
            model_provider=model_provider,
            os_client=os_client
        )

        # Query OpenSearch to verify bulk upload
        query_body = {"query": {"match_all": {}}}
        response = os_client.search(index=index_name, body=query_body)
        logger.info(
            f"Total records in index {index_name}: {response['hits']['total']['value']}"
        )
        logger.info(f"Partial response [:5]: {response['hits']['hits'][:5]}")
    else:
        logger.info("No data loading requested.")

    return {
        "statusCode": 200,
        "body": json.dumps("Lambda execution and data loading completed successfully."),
    }

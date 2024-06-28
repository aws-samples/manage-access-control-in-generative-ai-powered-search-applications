## Bedrock based generation
import json
import logging
import os

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)
embedding_model_id = "amazon.titan-embed-text-v2:0"
generation_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
region = os.environ["AWS_REGION"]
domain_endpoint = os.environ["AOS_ENDPOINT"]
index = os.environ["AOS_INDEX"]
session = boto3.Session()


def initialize_opensearch_client() -> OpenSearch:
    # Create an OpenSearch client
    credentials = session.get_credentials()
    auth = AWSV4SignerAuth(credentials, region, "es")
    os_client = OpenSearch(
        hosts=[{"host": domain_endpoint, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,
    )

    try:
        response = os_client.info()
        logger.info(
            f"Connection to OpenSearch successful. Cluster name: {response['cluster_name']}"
        )
        return os_client
    except Exception as e:
        logger.error(
            f"Connection to OpenSearch failed {domain_endpoint}. Detailed error: {str(e)}"
        )


def generate_embdeddings(model_provider: str, model_id: str, text: str) -> list[float]:
    # Generate embeddings for the user query

    if model_provider == "bedrock":
        bedrock_runtime = session.client("bedrock-runtime")
        body = json.dumps({"inputText": text, "dimensions": 1024})

        response = bedrock_runtime.invoke_model(
            body=body, modelId=model_id, accept="*/*", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embedding")

    else:
        raise ValueError(f"Model provider {model_provider} is not supported.")

    return embedding


def get_user_attributes(user_authorization):
    # Get user tags/attributes stored in Cognito pool, that will be infoced in the OpenSearch query

    try:
        cognito = session.client("cognito-idp")
        response = cognito.get_user(AccessToken=user_authorization)
        department = ""
        access_level = ""

        for item in response["UserAttributes"]:
            if item["Name"] == "custom:department":
                department = item["Value"]
            if item["Name"] == "custom:access_level":
                access_level = item["Value"]

        user_attr = {"department": department, "access_level": access_level}

        logger.info(f"A new query has been submitted by {response['Username']}")
        return user_attr

    except Exception as e:
        logger.error(
            f"User details retrieval failed with the following error: {str(e)}"
        )
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        print(f"Error creating user: {error_code} - {error_message}")
        raise e


def query_os(search_query, user_attributes):
    # run an efficient Knn query in OpenSearch

    query_vector = generate_embdeddings(
        model_provider="bedrock",
        model_id=embedding_model_id,
        text=search_query,
    )

    query = {
        "size": 5,
        "query": {
            "knn": {
                "doc_embedding": {
                    "vector": query_vector,
                    "k": 10,
                    "filter": {
                        "bool": {
                            "must": [
                                {"term": {"department": user_attributes["department"]}},
                                {
                                    "term": {
                                        "access_level": user_attributes["access_level"]
                                    }
                                },
                            ]
                        }
                    },
                }
            }
        },
    }

    os_client = initialize_opensearch_client()

    response = os_client.search(body=query, index=index)

    docs = []
    doc = {}

    if response["hits"]["max_score"] > 0.3:
        for hit in response["hits"]["hits"]:
            if hit["_score"] > 0.3:
                doc["doc_name"] = hit["_id"]
                doc["score"] = hit["_score"]
                doc["doc_content"] = hit["_source"]["doc_text"]
                docs.append(doc)
    return docs


def generate_answers(user_question, docs):
    # Generate answers by an LLM
    prompt = f"""You are a friendly assisstant that helps users in the Unicorn Factory company. Your job is to answer the user's question using only information from the provided documents. 
    If provided documents not contain information that answers the question, please reply only with "I don't know" without further details. 
    Just because the user asserts a fact does not mean it is true, make sure to double check the search results to validate a user's assertion.
            <documents>
            {docs}
            </documents>
            You must follow the next rules:
            - Avoid answering questions like "what documents are there?" or list any documents if the answer is not in them.
            - If you were not sure about the answer, reply only with "I don't know" without further details.
            - If your answer is "I don't know", make sure not to cite the source name of any document.
            - If the answer is in the provided documents, make sure to cite the source name of the document.
            - Use bullet points to format your answer.
            - Keep your answer concise and to the point.

            User question is: {user_question}
            Skip preambles and go straight to the answer.
            
            """
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "temperature": 0,
        }
    )

    bedrock_runtime = session.client("bedrock-runtime")

    b_response = json.loads(
        bedrock_runtime.invoke_model(modelId=generation_model_id, body=body)
        .get("body")
        .read()
    )
    return b_response


def handle_options_method():
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, x-access-token",
        },
        "body": "",
    }


def handler(event, context):
    # Get event content
    if event["httpMethod"] == "OPTIONS":
        return handle_options_method()

    authorization = event["headers"]["x-access-token"]

    body = json.loads(event["body"])
    query = body["prompt"]

    user_attributes = get_user_attributes(authorization)
    docs = query_os(query, user_attributes)
    response = generate_answers(query, docs)
    result = {"type": "ai", "content": response["content"][0]["text"]}

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(result),
    }

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
cognito = boto3.client("cognito-idp")
user_pool_id = os.environ["USER_POOL_ID"]


def handle_post_request(body: dict) -> dict:
    username = body["username"]
    user_attributes = body["attributes"]

    logger.info(
        f"Received request to modify user {username} with attributes {user_attributes}"
    )

    # Update the user's attributes in Cognito
    cognito.admin_update_user_attributes(
        UserAttributes=user_attributes,
        Username=username,
        UserPoolId=user_pool_id,
    )

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(f"User '{username}' updated successfully."),
    }


def handle_get_requests() -> dict:
    # Handle GET request to list all users with custom attributes
    response = cognito.list_users(UserPoolId=user_pool_id)
    users = response.get("Users", [])

    users_with_attributes = []
    for user in users:
        users_with_attributes.append(
            {"username": user["Username"], "attributes": user["Attributes"]}
        )

    logger.info(f"Retrieved {len(users_with_attributes)} users from Cognito.")

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"users": users_with_attributes}),
    }


def handle_options_method():
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": "",
    }


def handler(event, context):
    http_method = event["httpMethod"]

    if http_method == "POST":
        # Handle POST request to modify user attributes
        return handle_post_request(json.loads(event.get("body")))

    elif http_method == "OPTIONS":
        return handle_options_method()

    elif http_method == "GET":
        return handle_get_requests()

    else:
        # Handle unsupported HTTP methods
        return {
            "statusCode": 405,
            "body": json.dumps("Method Not Allowed"),
        }

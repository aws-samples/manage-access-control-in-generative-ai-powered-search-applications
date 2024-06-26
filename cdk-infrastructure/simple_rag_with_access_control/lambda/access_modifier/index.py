import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
cognito = boto3.client("cognito-idp")
user_pool_id = os.environ["USER_POOL_ID"]


def handle_post_request(body: dict) -> dict:
    username = body["username"]
    user_attributes = body["attributes"]
    user_attributes_modified = []
    for attr in user_attributes:
        user_attributes_modified.append({"Name": attr["name"], "Value": attr["value"]})

    logger.info(
        f"Received request to modify user {username} with attributes {user_attributes}"
    )

    # Update the user's attributes in Cognito
    cognito.admin_update_user_attributes(
        UserAttributes=user_attributes_modified,
        Username=username,
        UserPoolId=user_pool_id,
    )

    return {
        "statusCode": 200,
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
        "body": json.dumps({"users": users_with_attributes}),
    }


def handler(event, context):
    http_method = event["httpMethod"]

    if http_method == "POST":
        # Handle POST request to modify user attributes
        return handle_post_request(json.loads(event.get("body")))

    elif http_method == "GET":
        return handle_get_requests()

    else:
        # Handle unsupported HTTP methods
        return {
            "statusCode": 405,
            "body": json.dumps("Method Not Allowed"),
        }

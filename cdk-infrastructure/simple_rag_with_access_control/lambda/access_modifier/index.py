import os
import json
import boto3
import logging


def handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Get username and desired cognito attributes from the request body
    body = json.loads(event.get("body"))
    username = body["username"]
    user_attributes = body["attributes"]
    user_attributes_modified = []
    for attr in user_attributes:
        user_attributes_modified.append({
            "Name": attr["name"],
            "Value": attr["value"]
        })

    logger.info(
        f"Received request to modify user {username} with attributes {user_attributes}"
    )
    user_pool_id = os.environ["USER_POOL_ID"]

    # Set up the Cognito client
    cognito = boto3.client("cognito-idp")

    # Update the user's attributes in Cognito
    try:
        response = cognito.admin_update_user_attributes(
            UserAttributes=user_attributes_modified, Username=username, UserPoolId=user_pool_id
        )

        print(response)
    except Exception as e:
        logger.error(f"User modification failed with the following error: {str(e)}")
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        print(f"Error creating user: {error_code} - {error_message}")
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps(f"User '{username}' updated successfully."),
    }

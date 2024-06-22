- This Lambda function to be executed by the front end application to modify the assigned attriibutes to a user
- The Lambda expects the event to contain a body similar to the following:
```
{
  "body": {
    "username": "<USERNAME>",
    "userAttributes": {
      "Name": "custom:access_level",
      "Value": "privileged"
    }
  }
}

```
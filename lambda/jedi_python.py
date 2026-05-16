import json
from datetime import datetime, timezone


def lambda_handler(event, context):
    print("Incoming event:", json.dumps(event))

    params = event.get("queryStringParameters") or {}
    name = params.get("name", "Chewbacca")

    response = {
        "message": f"Welcome {name}. The Python Jedi Council accepts your request.",
        "runtime": "python-jedi",
        "side": "jedi",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("Response:", json.dumps(response))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response)
    }

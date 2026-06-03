import json
import os
from datetime import datetime, timezone

import boto3

# ==================================================
# CONFIGURATION
# ==================================================

TOKEN_TABLE_NAME = os.getenv("TOKEN_TABLE_NAME", "jedi-token-holocron")


# ==================================================
# HEADER LOOKUP
# ==================================================

def get_header(event, name):
    headers = event.get("headers") or {}
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return None


# ==================================================
# DYNAMODB TOKEN UPDATE
# ==================================================

def mark_token_used(token_id, route):
    table = boto3.resource("dynamodb").Table(TOKEN_TABLE_NAME)
    used_at = datetime.now(timezone.utc).isoformat()

    table.update_item(
        Key={"token_id": token_id},
        UpdateExpression="SET used = :used, used_at = :used_at, used_route = :route",
        ExpressionAttributeValues={
            ":used": True,
            ":used_at": used_at,
            ":route": route,
        },
    )

    return used_at


# ==================================================
# LAMBDA HANDLER
# ==================================================

def lambda_handler(event, context):
    print("Incoming event:", json.dumps(event))

    # Query string keeps the original Jedi route greeting behavior.
    params = event.get("queryStringParameters") or {}
    name = params.get("name", "Chewbacca")

    # x-token-id links this route invocation back to the helper-created record.
    token_id = get_header(event, "x-token-id")
    token_tracking = {
        "table": TOKEN_TABLE_NAME,
        "token_id": token_id,
        "status": "missing-token-id",
    }

    if token_id:
        try:
            used_at = mark_token_used(token_id, "jedi")
            token_tracking["status"] = "marked-used"
            token_tracking["used_at"] = used_at
        except Exception as exc:
            print(f"Token tracking update failed: {exc}")
            token_tracking["status"] = "update-failed"
            token_tracking["error"] = str(exc)

    # Return the original route response plus token tracking telemetry.
    response = {
        "message": f"Welcome {name}. The Python Jedi Council accepts your request.",
        "runtime": "python-jedi",
        "side": "jedi",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token_tracking": token_tracking,
    }

    print("Response:", json.dumps(response))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }

import os
from datetime import datetime, timedelta, timezone

import boto3

# ==================================================
# CONFIGURATION
# ==================================================

TOKEN_TABLE_NAME = os.getenv("TOKEN_TABLE_NAME", "jedi-token-holocron")
TOKEN_UNUSED_MINUTES = int(os.getenv("TOKEN_UNUSED_MINUTES", "10"))


# ==================================================
# TIMESTAMP PARSING
# ==================================================

def parse_issued_at(value):
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    issued_at = datetime.fromisoformat(value)
    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=timezone.utc)

    return issued_at.astimezone(timezone.utc)


# ==================================================
# DYNAMODB TABLE SCAN
# ==================================================

def iter_table_items(table):
    response = table.scan()
    yield from response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        yield from response.get("Items", [])


# ==================================================
# LAMBDA HANDLER
# ==================================================

def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TOKEN_TABLE_NAME)
    now = datetime.now(timezone.utc)
    cutoff = timedelta(minutes=TOKEN_UNUSED_MINUTES)

    scanned = 0
    alerts = 0

    for item in iter_table_items(table):
        scanned += 1

        if item.get("used") is not False:
            continue

        token_id = item.get("token_id", "<missing-token-id>")
        username = item.get("username", "<unknown-user>")
        issued_at_raw = item.get("issued_at")

        # Detector records need issued_at so age can be calculated correctly.
        if not issued_at_raw:
            print(f"Skipping token {token_id}: issued_at is missing")
            continue

        try:
            issued_at = parse_issued_at(issued_at_raw)
        except ValueError as exc:
            print(f"Skipping token {token_id}: issued_at is invalid: {exc}")
            continue

        age = now - issued_at
        if age > cutoff:
            alerts += 1
            # CloudWatch metric filters use this ALERT prefix.
            print(
                "ALERT: Token unused "
                f"for user {username}; token_id={token_id}; "
                f"issued_at={issued_at.isoformat()}; age_minutes={age.total_seconds() / 60:.1f}"
            )

    result = {
        "table": TOKEN_TABLE_NAME,
        "unused_after_minutes": TOKEN_UNUSED_MINUTES,
        "scanned": scanned,
        "alerts": alerts,
    }

    print(f"Detector result: {result}")
    return result

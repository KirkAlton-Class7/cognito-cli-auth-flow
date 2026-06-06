# Unused Token Detector Lab

This lab extends the Cognito auth flow by adding token-use telemetry and an unused-token detector. The goal is to practice editing code and seeing why each change exists. You can edit directly in AWS, but the recommended flow is to copy starter code into the sandbox, edit locally, then add the edited code in AWS and deploy. The quick-deployment files are provided as finished references after the manual path. Use the runbook when you want the concise quick deployment flow.

Ready code path lives in `../../../docs/deploy-token-detector-runbook.md`.

## Theme Map

| Existing lab item | unused token detector name |
| --- | --- |
| `/prod/jedi` Python route | Jedi Council route |
| `/prod/sith` Node route | Sith route |
| Token tracking table | Jedi token holocron |
| Unused token detector Lambda | unused token detector |
| Alert topic | Jedi auth alerts |

## Lab Assets

| Path | Purpose |
| --- | --- |
| `sandbox/` | Empty student workspace. Copy starter files here, edit locally, then add the edited code in AWS. |
| `sandbox/scripts/` | Local copies of helper scripts copied from `shared/scripts/`. |
| `sandbox/lambda-code/` | Local copies of Lambda code copied from `shared/lambda-code/`, plus the new detector Lambda you create in this lab. |
| `quick-deployment/get_token.py` | Finished token helper reference. |
| `quick-deployment/jedi_python_token_tracker.py` | Finished Jedi Python route Lambda reference. |
| `quick-deployment/sith_node_token_tracker.js` | Finished Sith Node route Lambda reference. |
| `quick-deployment/unused_token_detector.py` | Finished detector Lambda reference. |

> [!IMPORTANT]
> Do not pre-fill `sandbox/` with the quick-deployment files. The sandbox is where students copy starter files from `shared/`, make the lab edits, then add the edited code in AWS.

## 1. Create And Load The Environment File

An environment file helps simplify deployment and provides a record of planned values and resource outputs. You will copy the dotenv template, rename the copy to `.env`, update initial values, then reload it before running commands that depend on those values.

Copy the template:

```bash
cp "$LAB_REPO/deploy-token-detector/labs/token-detector/env.example" \
  "$LAB_REPO/deploy-token-detector/labs/token-detector/.env"
```

Set the environment file path:

```bash
export LAB_ENV="$LAB_REPO/deploy-token-detector/labs/token-detector/.env"
```

Get the AWS account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

Open `.env` in VS Code or your editor of choice:

```bash
code "$LAB_ENV"
```

In `.env`, update the foundational inputs and API base value before building:

```bash
LAB_REPO="/Users/kirk/devsecops/cognito-cli-auth-flow"
AWS_ACCOUNT_ID="123456789012"
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-rest"
API_BASE="https://<API_ID>.execute-api.${AWS_REGION}.amazonaws.com/prod"
```

Save `.env`, then load it for the build phase:

```bash
set -a
source "$LAB_ENV"
set +a
```

Validate the starting values:

```bash
echo "$PROJECT_NAME"
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
echo "$TOKEN_TABLE_NAME"
echo "$TOKEN_DETECTOR_FUNCTION"
echo "$API_BASE"
```

## 2. Create The Jedi Token Holocron Table

Console navigation: **DynamoDB** -> **Tables** -> **Create table**.

Use these values:

| Setting | Value |
| --- | --- |
| Table name | value from `TOKEN_TABLE_NAME`, for example `chewbacca-auth-rest-jedi-token-holocron` |
| Partition key | `token_id` |
| Partition key type | String |
| Capacity mode | On-demand |

Each token record will look like this:

```json
{
  "token_id": "37c5c4d6-5f2d-4838-b3c1-3b46f66d2a0",
  "username": "chewbacca",
  "issued_at": "2026-06-02T23:12:30.403221+00:00",
  "used": false,
  "source": "get_token.py"
}
```

Equivalent CLI reference:

```bash
aws dynamodb create-table \
  --table-name "$TOKEN_TABLE_NAME" \
  --attribute-definitions AttributeName=token_id,AttributeType=S \
  --key-schema AttributeName=token_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$AWS_REGION"
```

Validation:

```bash
aws dynamodb describe-table \
  --table-name "$TOKEN_TABLE_NAME" \
  --query 'Table.TableStatus' \
  --output text \
  --region "$AWS_REGION"
```

## 3. Give The Existing Route Lambdas DynamoDB Permission

The existing route Lambdas are named from the repo's Jedi/Sith pattern:

```bash
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
```

Attach this inline policy to the role used by those functions.

Console navigation: **IAM** -> **Roles** -> open the Lambda role -> **Add permissions** -> **Create inline policy** -> JSON.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:<ACCOUNT_ID>:table/<TOKEN_TABLE_NAME>"
    }
  ]
}
```

Equivalent CLI reference:

```bash
aws iam put-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name "${PROJECT_NAME}-jedi-token-holocron-access" \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"dynamodb:GetItem\",
          \"dynamodb:PutItem\",
          \"dynamodb:UpdateItem\",
          \"dynamodb:Scan\",
          \"dynamodb:Query\"
        ],
        \"Resource\": \"arn:aws:dynamodb:${AWS_REGION}:${AWS_ACCOUNT_ID}:table/${TOKEN_TABLE_NAME}\"
      }
    ]
  }" \
  --region "$AWS_REGION"
```

## 4. Copy And Update The Token Helper In The Sandbox

The sandbox starts empty on purpose. Copy the original token helper from `shared/scripts/` into the lab sandbox, then edit the sandbox copy.

```bash
mkdir -p deploy-token-detector/labs/token-detector/sandbox/scripts
cp shared/scripts/flavor_get_token.py deploy-token-detector/labs/token-detector/sandbox/scripts/get_token.py
```

Keep the existing Jedi/Sith route logic:

```python
# ==================================================
# CONFIGURATION
# ==================================================

PYTHON_ROUTE = os.getenv("PYTHON_ROUTE", "jedi")
NODE_ROUTE = os.getenv("NODE_ROUTE", "sith")
NAME_QUERY = "?name="
NAME = os.getenv("CHEWBACCA_NAME", "Chewbacca")
```

It adds a new import:

```python
# Place this at the top of your script with imports
import uuid
```

Make sure the script has a table name setting near the other configuration values:

```python
# ==================================================
# CONFIGURATION
# ==================================================

TOKEN_TABLE_NAME = (
    os.getenv("TOKEN_TABLE_NAME")
    or os.getenv("DYNAMODB_TABLE_NAME")
    or "jedi-token-holocron"
)
```

And adds a new token record:

```python
# Add this to the end of your script.
# ==================================================
# DYNAMODB - WRITE TOKEN ATTRIBUTES TO DB
# ==================================================
# Create one tracking record for the token this helper just generated.
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TOKEN_TABLE_NAME)

token_id = str(uuid.uuid4())
now = datetime.now(timezone.utc)

table.put_item(
    Item={
        "token_id": token_id,
        "username": username,
        "issued_at": now.isoformat(),
        "used": False,
        "source": "get_token.py"
    }
)
```

Also update the printed curl examples so they include the token ID header:

```bash
-H "x-token-id: {token_id}"
```

The finished reference implementation is here:

```bash
deploy-token-detector/labs/token-detector/quick-deployment/get_token.py
```

Run the sandbox copy:

```bash
cd "$LAB_REPO"

AWS_REGION="$AWS_REGION" \
AWS_DEFAULT_REGION="$AWS_REGION" \
TOKEN_TABLE_NAME="$TOKEN_TABLE_NAME" \
API_BASE="$API_BASE" \
python3 deploy-token-detector/labs/token-detector/sandbox/scripts/get_token.py
```

Expected output includes:

```text
========== JEDI TOKEN HOLOCRON RECORD CREATED ==========
Table: chewbacca-auth-rest-jedi-token-holocron
token_id: <uuid>
username: chewbacca
used: False
```

## 5. Copy And Update The Jedi And Sith Route Lambdas

Copy the original route Lambda code from `shared/lambda-code/` into the lab sandbox, then edit the sandbox copies. You can make the edits directly in AWS, but copying them locally first gives you a clean file to inspect, package, and reuse.

```bash
mkdir -p deploy-token-detector/labs/token-detector/sandbox/lambda-code
cp shared/lambda-code/jedi_python.py deploy-token-detector/labs/token-detector/sandbox/lambda-code/jedi_python_token_tracker.py
cp shared/lambda-code/sith_node.js deploy-token-detector/labs/token-detector/sandbox/lambda-code/sith_node_token_tracker.js
```

After editing, add the updated code to your existing AWS route Lambdas rather than creating brand-new route functions.

| Route | Existing Lambda name pattern | Finished reference code |
| --- | --- | --- |
| `/prod/jedi` | `${PROJECT_NAME}-jedi-python` | `deploy-token-detector/labs/token-detector/quick-deployment/jedi_python_token_tracker.py` |
| `/prod/sith` | `${PROJECT_NAME}-sith-node` | `deploy-token-detector/labs/token-detector/quick-deployment/sith_node_token_tracker.js` |

Set this environment variable on both route Lambdas:

```text
TOKEN_TABLE_NAME=<value from TOKEN_TABLE_NAME>
```

### Manual Jedi Python Route Update

Open the existing Jedi route Lambda, `${PROJECT_NAME}-jedi-python`, and add these imports at the top:

```python
import os
import boto3
```

Add the table name after the imports:

```python
# ==================================================
# CONFIGURATION
# ==================================================

TOKEN_TABLE_NAME = os.getenv("TOKEN_TABLE_NAME", "jedi-token-holocron")
```

Add these helper functions above `lambda_handler`:

```python
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
```

Inside `lambda_handler`, after the `name` value is read from query parameters, add:

```python
# ==================================================
# TOKEN TRACKING
# ==================================================
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
```

Add `token_tracking` to the JSON response body:

```python
# Return the original route response plus token tracking telemetry.
"token_tracking": token_tracking,
```

### Manual Sith Node Route Update

Open the existing Sith route Lambda, `${PROJECT_NAME}-sith-node`, and add this import at the top:

```javascript
const { DynamoDBClient, UpdateItemCommand } = require("@aws-sdk/client-dynamodb");
```

Add the DynamoDB client and table name after the import:

```javascript
// CONFIGURATION
const client = new DynamoDBClient({});
const TOKEN_TABLE_NAME = process.env.TOKEN_TABLE_NAME || "jedi-token-holocron";
```

Add these helper functions above `exports.handler`:

```javascript
// HEADER LOOKUP
function getHeader(event, name) {
    const headers = event.headers || {};
    const wanted = name.toLowerCase();

    for (const [key, value] of Object.entries(headers)) {
        if (key.toLowerCase() === wanted) {
            return value;
        }
    }

    return null;
}

// DYNAMODB TOKEN UPDATE
async function markTokenUsed(tokenId, route) {
    const usedAt = new Date().toISOString();

    await client.send(
        new UpdateItemCommand({
            TableName: TOKEN_TABLE_NAME,
            Key: {
                token_id: { S: tokenId },
            },
            UpdateExpression: "SET used = :used, used_at = :used_at, used_route = :route",
            ExpressionAttributeValues: {
                ":used": { BOOL: true },
                ":used_at": { S: usedAt },
                ":route": { S: route },
            },
        })
    );

    return usedAt;
}
```

Inside `exports.handler`, after the `name` value is read from query parameters, add:

```javascript
// TOKEN TRACKING
// x-token-id links this route invocation back to the helper-created record.
const tokenId = getHeader(event, "x-token-id");
const tokenTracking = {
    table: TOKEN_TABLE_NAME,
    token_id: tokenId,
    status: "missing-token-id",
};

if (tokenId) {
    try {
        const usedAt = await markTokenUsed(tokenId, "sith");
        tokenTracking.status = "marked-used";
        tokenTracking.used_at = usedAt;
    } catch (error) {
        console.log("Token tracking update failed:", error);
        tokenTracking.status = "update-failed";
        tokenTracking.error = String(error);
    }
}
```

Add `token_tracking` to the JSON response object:

```javascript
// Return the original route response plus token tracking telemetry.
token_tracking: tokenTracking,
```

Validation:

```bash
aws dynamodb get-item \
  --table-name "$TOKEN_TABLE_NAME" \
  --key '{"token_id":{"S":"<TOKEN_ID>"}}' \
  --region "$AWS_REGION"
```

Expected result after calling `/prod/jedi` or `/prod/sith` with `x-token-id`:

```text
used: true
used_route: jedi
```

or:

```text
used: true
used_route: sith
```

## 6. Create The Unused Token Detector Lambda

There is no starter detector Lambda in `shared/`; this is the new Lambda for the lab. Create it locally in the sandbox first, then add it in AWS and deploy it.

```bash
touch deploy-token-detector/labs/token-detector/sandbox/lambda-code/unused_token_detector.py
```

Create a new Lambda for detection:

| Setting | Value |
| --- | --- |
| Function name | value from `TOKEN_DETECTOR_FUNCTION`, for example `chewbacca-auth-rest-unused-token-detector` |
| Runtime | Python 3.12 |
| Handler | `unused_token_detector.lambda_handler` |
| Environment variable | `TOKEN_TABLE_NAME=<TOKEN_TABLE_NAME>` |
| Optional environment variable | `TOKEN_UNUSED_MINUTES=10` |

The finished detector code is available in `quick-deployment/unused_token_detector.py` for comparison after you complete the manual edit path. Use the ready runbook at `../../../docs/deploy-token-detector-runbook.md` when you want the concise quick deployment flow.

Test the detector:

```bash
aws lambda invoke \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/unused-token-detector-response.json \
  --region "$AWS_REGION"

jq . /tmp/unused-token-detector-response.json
```

Expected CloudWatch log line when an old token is unused:

```text
ALERT: Token unused for user chewbacca
```

## 7. Create The EventBridge Schedule

Use an EventBridge **schedule**, not a classic rule.

Console navigation: **Amazon EventBridge** -> **Scheduler** -> **Create schedule**.

Use these values:

| Setting | Value |
| --- | --- |
| Schedule name | value from `TOKEN_SCAN_SCHEDULE` |
| Schedule pattern | Rate-based schedule |
| Rate | `5 minutes` |
| Target | Lambda |
| Function | value from `TOKEN_DETECTOR_FUNCTION` |

## 8. Create The Alert Path

Start with CloudWatch logs. Then turn detector log lines into a metric and alarm.

Create an SNS topic named from `TOKEN_ALERT_TOPIC`, subscribe your email, and confirm the subscription.

Create a CloudWatch metric filter on `/aws/lambda/<TOKEN_DETECTOR_FUNCTION>`:

| Setting | Value |
| --- | --- |
| Filter pattern | `"ALERT: Token unused"` |
| Filter name | value from `TOKEN_ALERT_FILTER_NAME` |
| Metric namespace | value from `TOKEN_ALERT_METRIC_NAMESPACE` |
| Metric name | value from `TOKEN_ALERT_METRIC_NAME` |
| Metric value | `1` |

Create an alarm:

| Setting | Value |
| --- | --- |
| Metric | `UnusedTokenAlertCount` |
| Statistic | Sum |
| Period | 5 minutes |
| Condition | Greater than 0 |
| Missing data | Treat missing data as good |
| Action | Send notification to `TOKEN_ALERT_TOPIC` |

## 9. Practice The Detection Flow

Run the `get_token.py` script and do not call either API route. Wait more than `TOKEN_UNUSED_MINUTES`, then invoke the detector or wait for the schedule.

Expected result:

```text
ALERT: Token unused for user chewbacca
```

Run the `get_token.py` script again, then call the printed `/prod/jedi` or `/prod/sith` curl command with `x-token-id`.

Expected result:

```text
Token is marked used in DynamoDB
Detector does not alert for that token
```

## Validation Checklist

Use this checklist before you consider the token detector lab complete:

- [ ] Start from a working REST or HTTPS Cognito auth flow.
- [ ] Copy `env.example` to `.env`, update planned values, and reload it before dependent commands.
- [ ] Create the DynamoDB token table with `token_id` as the partition key.
- [ ] Add the DynamoDB access policy to the Lambda role used by the route and detector functions.
- [ ] Copy starter helper code into `sandbox/scripts/` and add the `uuid` import.
- [ ] Add a DynamoDB token record after a token is issued, with `used` set to `False`.
- [ ] Preserve the routing logic from the original token helper script.
- [ ] Print curl examples that include the generated `x-token-id` header.
- [ ] Copy starter Jedi and Sith route code into `sandbox/lambda-code/`.
- [ ] Update the Python route Lambda to read `x-token-id` and mark matching records used.
- [ ] Update the Node.js route Lambda to read `x-token-id` and mark matching records used.
- [ ] Preserve the original Jedi and Sith route response behavior after adding token telemetry.
- [ ] Create or deploy `unused_token_detector.py` with the token table environment variable.
- [ ] Run `get_token.py` and confirm a new DynamoDB item is created.
- [ ] Call a protected Jedi or Sith route with `x-token-id` and confirm DynamoDB marks the token used.
- [ ] Generate a token and intentionally do not use it.
- [ ] Invoke the detector after the unused threshold and confirm `ALERT: Token unused` appears in CloudWatch Logs.
- [ ] Create the EventBridge Scheduler rule for recurring detector scans.
- [ ] Create the SNS topic, CloudWatch metric filter, and CloudWatch alarm for unused-token alerts.
- [ ] Run the lab teardown from the matching lab teardown file when you are ready to remove the detector resources.

## Concept Takeaways

- Cognito can issue valid tokens that are never used against protected APIs; token issuance and token usage are different events.
- DynamoDB gives each issued token a durable tracking record keyed by `token_id`.
- The `x-token-id` header connects an API call back to the token-helper record without changing Cognito itself.
- The Jedi and Sith route Lambdas should keep their original route behavior while adding token-use telemetry.
- The detector Lambda turns stored token metadata into an operational signal by finding old records where `used` is still `False`.
- CloudWatch metric filters convert detector log lines into metrics, and alarms turn those metrics into notifications.
- EventBridge Scheduler makes detection recurring instead of manual.
- This pattern practices security observability: proving not just who authenticated, but whether the issued credential was used.

## Final Check

You are ready to leave this token detector lab when you can explain the full flow without looking:

```text
Cognito issues JWT tokens
get_token.py records issued token metadata in DynamoDB
Protected routes receive x-token-id after API Gateway authorization succeeds
Jedi and Sith Lambdas mark matching token records as used
unused_token_detector.py scans for old unused token records
CloudWatch metric filters turn detector logs into alert signals
SNS delivers the unused-token notification path
```

## References

[Boto3 Documentation - put_item](https://docs.aws.amazon.com/boto3/latest/reference/services/dynamodb/table/put_item.html)  
[Working With Items and Attributes in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html)  
[Filter Pattern Syntax for Metric Filters, Subscription Filters, Filter Log Events, and Live Tail](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html#regex-expressions)

[Amazon DynamoDB data model](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html)  
[EventBridge Scheduler user guide](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html)  
[Amazon SNS topics](https://docs.aws.amazon.com/sns/latest/dg/sns-create-topic.html)  
[CloudWatch metric filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html)

### AWS CLI Command References

Every AWS CLI command used in this lab is linked below to the direct AWS command reference page.

| Command | AWS CLI reference |
| --- | --- |
| `aws sts get-caller-identity` | [sts get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |
| `aws iam put-role-policy` | [iam put-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/put-role-policy.html) |
| `aws dynamodb create-table` | [dynamodb create-table](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/create-table.html) |
| `aws dynamodb describe-table` | [dynamodb describe-table](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/describe-table.html) |
| `aws dynamodb get-item` | [dynamodb get-item](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/get-item.html) |
| `aws lambda create-function` | [lambda create-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/create-function.html) |
| `aws lambda invoke` | [lambda invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html) |

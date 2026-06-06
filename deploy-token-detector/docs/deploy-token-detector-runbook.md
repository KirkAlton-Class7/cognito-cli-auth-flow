# Unused Token Detector Runbook

This runbook deploys token-use tracking and unused-token detection for the Cognito auth flow. Use the ready scripts and Lambda code in this folder, package them, deploy them, and validate the alert flow.

## What This Deploys

- Cognito token helper
- DynamoDB token record
- API Gateway /prod/jedi or /prod/sith
- route Lambda marks token used
- detector Lambda scans for stale unused tokens
- CloudWatch logs and optional SNS alarm

## Deployment Assets

| Path | Purpose |
| --- | --- |
| `scripts/get_token.py` | Token helper that writes token records and prints Jedi/Sith curl examples. |
| `lambda-code/jedi_python_token_tracker.py` | Jedi Python route Lambda with token-used tracking. |
| `lambda-code/sith_node_token_tracker.js` | Sith Node route Lambda with token-used tracking. |
| `lambda-code/unused_token_detector.py` | Detector Lambda that logs unused token alerts. |

## 1. Create And Load The Environment File

An environment file helps simplify deployment and provides a record of planned values and resource outputs. You will copy the dotenv template, rename the copy to `.env`, update initial values, then reload it before running commands that depend on those values.

Copy the template:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
cd "$REPO_ROOT"

cp "$REPO_ROOT/deploy-token-detector/env.example" \
  "$REPO_ROOT/deploy-token-detector/.env"
```

Set the environment file path:

```bash
export ENV_FILE="$REPO_ROOT/deploy-token-detector/.env"
```

Get the AWS account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

Open `.env` in VS Code or your editor of choice:

```bash
code "$ENV_FILE"
```

In `.env`, update the foundational inputs and API base value before building:

```bash
REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
AWS_ACCOUNT_ID="123456789012"
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-rest"
API_BASE="https://<API_ID>.execute-api.${AWS_REGION}.amazonaws.com/prod"
```

Save `.env`, then load it for the deployment phase:

```bash
set -a
source "$ENV_FILE"
set +a
```

Validate the starting values:

```bash
echo "$AWS_REGION"
echo "$AWS_ACCOUNT_ID"
echo "$PROJECT_NAME"
echo "$TOKEN_TABLE_NAME"
echo "$TOKEN_DETECTOR_FUNCTION"
echo "$API_BASE"
```

## 2. Create The DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name "$TOKEN_TABLE_NAME" \
  --attribute-definitions AttributeName=token_id,AttributeType=S \
  --key-schema AttributeName=token_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$AWS_REGION"
```

Wait until the table is active:

```bash
aws dynamodb wait table-exists \
  --table-name "$TOKEN_TABLE_NAME" \
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

Expected:

```text
ACTIVE
```

## 3. Add DynamoDB Access To The Existing Lambda Role

Attach DynamoDB access to the existing Jedi/Sith route Lambda role.

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

## 4. Deploy The Updated Route Lambdas

Package the Jedi Python route Lambda:

```bash
cd "$REPO_ROOT/deploy-token-detector/lambda-code"
zip jedi-python-token-tracker.zip jedi_python_token_tracker.py
```

Update the existing Jedi route function:

```bash
aws lambda update-function-code \
  --function-name "$JEDI_FUNCTION" \
  --zip-file fileb://jedi-python-token-tracker.zip \
  --region "$AWS_REGION"

aws lambda update-function-configuration \
  --function-name "$JEDI_FUNCTION" \
  --handler jedi_python_token_tracker.lambda_handler \
  --environment "Variables={TOKEN_TABLE_NAME=${TOKEN_TABLE_NAME}}" \
  --region "$AWS_REGION"
```

Package the Sith Node route Lambda:

```bash
zip sith-node-token-tracker.zip sith_node_token_tracker.js
```

Update the existing Sith route function:

```bash
aws lambda update-function-code \
  --function-name "$SITH_FUNCTION" \
  --zip-file fileb://sith-node-token-tracker.zip \
  --region "$AWS_REGION"

aws lambda update-function-configuration \
  --function-name "$SITH_FUNCTION" \
  --handler sith_node_token_tracker.handler \
  --environment "Variables={TOKEN_TABLE_NAME=${TOKEN_TABLE_NAME}}" \
  --region "$AWS_REGION"
```

Validation:

```bash
aws lambda get-function-configuration \
  --function-name "$JEDI_FUNCTION" \
  --query '{FunctionName:FunctionName,Handler:Handler,Table:Environment.Variables.TOKEN_TABLE_NAME}' \
  --region "$AWS_REGION"

aws lambda get-function-configuration \
  --function-name "$SITH_FUNCTION" \
  --query '{FunctionName:FunctionName,Handler:Handler,Table:Environment.Variables.TOKEN_TABLE_NAME}' \
  --region "$AWS_REGION"
```

## 5. Deploy The Detector Lambda

Package the detector:

```bash
cd "$REPO_ROOT/deploy-token-detector/lambda-code"
zip unused-token-detector.zip unused_token_detector.py
```

Create the detector Lambda:

```bash
aws lambda create-function \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --runtime python3.12 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler unused_token_detector.lambda_handler \
  --zip-file fileb://unused-token-detector.zip \
  --environment "Variables={TOKEN_TABLE_NAME=${TOKEN_TABLE_NAME},TOKEN_UNUSED_MINUTES=10}" \
  --region "$AWS_REGION"
```

If the function already exists, update it instead:

```bash
aws lambda update-function-code \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --zip-file fileb://unused-token-detector.zip \
  --region "$AWS_REGION"

aws lambda update-function-configuration \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --handler unused_token_detector.lambda_handler \
  --environment "Variables={TOKEN_TABLE_NAME=${TOKEN_TABLE_NAME},TOKEN_UNUSED_MINUTES=10}" \
  --region "$AWS_REGION"
```

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

## 6. Create The EventBridge Schedule

Use EventBridge Scheduler.

```bash
export TOKEN_DETECTOR_ARN=$(aws lambda get-function \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region "$AWS_REGION")
```

Allow Scheduler to invoke the detector:

```bash
aws lambda add-permission \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --statement-id "${TOKEN_SCAN_SCHEDULE}-invoke" \
  --action lambda:InvokeFunction \
  --principal scheduler.amazonaws.com \
  --source-arn "arn:aws:scheduler:${AWS_REGION}:${AWS_ACCOUNT_ID}:schedule/default/${TOKEN_SCAN_SCHEDULE}" \
  --region "$AWS_REGION"
```

Create the schedule in the console:

- Amazon EventBridge
- Scheduler
- Create schedule
- Schedule name: value from TOKEN_SCAN_SCHEDULE
- Schedule pattern: rate(5 minutes)
- Target: Lambda
- Function: value from TOKEN_DETECTOR_FUNCTION

## 7. Configure CloudWatch And SNS Alerts

Create the SNS topic:

```bash
aws sns create-topic \
  --name "$TOKEN_ALERT_TOPIC" \
  --region "$AWS_REGION"
```

Export the topic ARN:

```bash
export TOKEN_ALERT_TOPIC_ARN=$(aws sns list-topics \
  --query "Topics[?ends_with(TopicArn, ':${TOKEN_ALERT_TOPIC}')].TopicArn | [0]" \
  --output text \
  --region "$AWS_REGION")
```

Subscribe an email endpoint:

```bash
aws sns subscribe \
  --topic-arn "$TOKEN_ALERT_TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "YOUR-EMAIL@example.com" \
  --region "$AWS_REGION"
```

Confirm the email subscription before expecting notifications.

Create the metric filter:

```bash
aws logs put-metric-filter \
  --log-group-name "/aws/lambda/${TOKEN_DETECTOR_FUNCTION}" \
  --filter-name "$TOKEN_ALERT_FILTER_NAME" \
  --filter-pattern '"ALERT: Token unused"' \
  --metric-transformations \
    metricName="$TOKEN_ALERT_METRIC_NAME",metricNamespace="$TOKEN_ALERT_METRIC_NAMESPACE",metricValue=1 \
  --region "$AWS_REGION"
```

Create the alarm:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "$TOKEN_ALERT_ALARM_NAME" \
  --metric-name "$TOKEN_ALERT_METRIC_NAME" \
  --namespace "$TOKEN_ALERT_METRIC_NAMESPACE" \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 0 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "$TOKEN_ALERT_TOPIC_ARN" \
  --region "$AWS_REGION"
```

## 8. Validate Token Tracking

Run the `get_token.py` script:

```bash
cd "$REPO_ROOT"

AWS_REGION="$AWS_REGION" \
AWS_DEFAULT_REGION="$AWS_REGION" \
TOKEN_TABLE_NAME="$TOKEN_TABLE_NAME" \
API_BASE="$API_BASE" \
python3 deploy-token-detector/scripts/get_token.py
```

Copy the printed `token_id`, then run one of the printed curl commands. Confirm DynamoDB updated the token:

```bash
aws dynamodb get-item \
  --table-name "$TOKEN_TABLE_NAME" \
  --key '{"token_id":{"S":"<TOKEN_ID>"}}' \
  --region "$AWS_REGION"
```

Expected:

```text
used: true
used_route: jedi
```

or:

```text
used: true
used_route: sith
```

Validate unused-token detection by generating a token and not calling either route. After more than `TOKEN_UNUSED_MINUTES`, invoke the detector or wait for the schedule.

Expected detector log:

```text
ALERT: Token unused for user chewbacca
```

## Final Check

You have completed this runbook when you can explain this flow without looking:

`get_token.py` creates a DynamoDB token record with a unique `token_id`  
The helper prints Jedi and Sith curl commands that carry `x-token-id`  
The Jedi and Sith route Lambdas preserve their original routing behavior  
The route Lambdas mark the matching token record as used  
`unused_token_detector.py` scans for old unused token records  
CloudWatch logs show `ALERT: Token unused` for stale unused tokens  
The metric filter turns detector log lines into a CloudWatch metric  
The alarm can notify through SNS when unused-token alerts appear

## References

[Boto3 Documentation - put_item](https://docs.aws.amazon.com/boto3/latest/reference/services/dynamodb/table/put_item.html)  
[Working With Items and Attributes in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html)  
[Filter Pattern Syntax for Metric Filters, Subscription Filters, Filter Log Events, and Live Tail](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html#regex-expressions)

### AWS CLI Command References

Every AWS CLI command used in this runbook is linked below to the direct AWS command reference page.

| Command | AWS CLI reference |
| --- | --- |
| `aws sts get-caller-identity` | [sts get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |
| `aws iam put-role-policy` | [iam put-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/put-role-policy.html) |
| `aws dynamodb create-table` | [dynamodb create-table](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/create-table.html) |
| `aws dynamodb wait table-exists` | [dynamodb wait table-exists](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/wait/table-exists.html) |
| `aws dynamodb describe-table` | [dynamodb describe-table](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/describe-table.html) |
| `aws dynamodb get-item` | [dynamodb get-item](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/get-item.html) |
| `aws lambda update-function-code` | [lambda update-function-code](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html) |
| `aws lambda update-function-configuration` | [lambda update-function-configuration](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-configuration.html) |
| `aws lambda create-function` | [lambda create-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/create-function.html) |
| `aws lambda invoke` | [lambda invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html) |
| `aws lambda get-function` | [lambda get-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function.html) |
| `aws lambda add-permission` | [lambda add-permission](https://docs.aws.amazon.com/cli/latest/reference/lambda/add-permission.html) |
| `aws sns create-topic` | [sns create-topic](https://docs.aws.amazon.com/cli/latest/reference/sns/create-topic.html) |
| `aws sns list-topics` | [sns list-topics](https://docs.aws.amazon.com/cli/latest/reference/sns/list-topics.html) |
| `aws sns subscribe` | [sns subscribe](https://docs.aws.amazon.com/cli/latest/reference/sns/subscribe.html) |
| `aws logs put-metric-filter` | [logs put-metric-filter](https://docs.aws.amazon.com/cli/latest/reference/logs/put-metric-filter.html) |
| `aws cloudwatch put-metric-alarm` | [cloudwatch put-metric-alarm](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/put-metric-alarm.html) |

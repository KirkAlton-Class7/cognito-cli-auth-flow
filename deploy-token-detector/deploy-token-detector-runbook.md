# Unused Token Detector Runbook

This runbook deploys token-use tracking and unused-token detection for the Chewbacca Cognito auth lab. It is the production-style path: use the ready scripts and Lambda code in this folder, package them, deploy them, and validate the alert flow.

For the hands-on editing lab, use `../LABS/jedi-token-detector/jedi-token-detector-lab.md`.

## What This Deploys

```text
Cognito token helper
  -> DynamoDB token record
  -> API Gateway /prod/jedi or /prod/sith
  -> route Lambda marks token used
  -> detector Lambda scans for stale unused tokens
  -> CloudWatch logs and optional SNS alarm
```

## Deployment Assets

| Path | Purpose |
| --- | --- |
| `scripts/get_token.py` | Token helper that writes token records and prints Jedi/Sith curl examples. |
| `lambda-code/jedi_python_token_tracker.py` | Jedi Python route Lambda with token-used tracking. |
| `lambda-code/sith_node_token_tracker.js` | Sith Node route Lambda with token-used tracking. |
| `lambda-code/unused_token_detector.py` | Detector Lambda that logs unused token alerts. |

## 1. Export Deployment Values

Use the same `PROJECT_NAME` as the API lab you already deployed.

```bash
export LAB_REPO="/Users/kirk/devsecops/cognito-auth-lab"
cd "$LAB_REPO"

export AWS_REGION="us-east-1"
export PROJECT_NAME="chewbacca-auth-rest"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"

export TOKEN_TABLE_NAME="${PROJECT_NAME}-jedi-token-holocron"
export TOKEN_DETECTOR_FUNCTION="${PROJECT_NAME}-unused-token-detector"
export TOKEN_SCAN_SCHEDULE="${PROJECT_NAME}-unused-token-check"
export TOKEN_ALERT_TOPIC="${PROJECT_NAME}-auth-alerts"

export TOKEN_ALERT_FILTER_NAME="${PROJECT_NAME}-unused-token-filter"
export TOKEN_ALERT_METRIC_NAMESPACE="${PROJECT_NAME}/auth-security"
export TOKEN_ALERT_METRIC_NAME="UnusedTokenAlertCount"
export TOKEN_ALERT_ALARM_NAME="${PROJECT_NAME}-unused-token-alarm"

# API_BASE includes /prod, matching scripts/get_token.py.
export API_BASE="https://<API_ID>.execute-api.${AWS_REGION}.amazonaws.com/prod"
```

Export AWS identifiers:

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

export LAMBDA_ROLE_ARN=$(aws iam get-role \
  --role-name "$LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text)
```

Validation:

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
cd "$LAB_REPO/deploy-token-detector/lambda-code"
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
cd "$LAB_REPO/deploy-token-detector/lambda-code"
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

```text
Amazon EventBridge -> Scheduler -> Create schedule
Schedule name: value from TOKEN_SCAN_SCHEDULE
Schedule pattern: rate(5 minutes)
Target: Lambda
Function: value from TOKEN_DETECTOR_FUNCTION
```

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

Run the token helper:

```bash
cd "$LAB_REPO"

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

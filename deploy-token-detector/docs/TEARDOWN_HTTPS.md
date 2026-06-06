# Token Detector HTTPS Teardown

Use this to tear down the HTTPS Cognito auth deployment plus the unused-token detector add-on. Skip any command for a resource you did not create.

> [!WARNING]
> These commands delete API Gateway, Lambda, Cognito, DynamoDB, EventBridge Scheduler, CloudWatch, SNS, and IAM resources. Confirm you are using the HTTPS values before running teardown.

## 1. Create And Load The Environment File

An environment file helps simplify teardown and provides a record of planned values and resource outputs. Copy the dotenv template, rename the copy to `.env`, update the values for the environment you want to remove, then reload it before running commands that depend on those values.

Copy the template if `.env` does not already exist:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
export ENV_FILE="$REPO_ROOT/deploy-token-detector/.env"

cp "$REPO_ROOT/deploy-token-detector/env.example" "$ENV_FILE"
```

Open `.env` and confirm these values match the resources you want to remove:

```bash
code "$ENV_FILE"
```

```bash
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-http"
JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
SITH_FUNCTION="${PROJECT_NAME}-sith-node"
TOKEN_DETECTOR_FUNCTION="${PROJECT_NAME}-unused-token-detector"
LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"
API_NAME="${PROJECT_NAME}-api"
USER_POOL_NAME="${PROJECT_NAME}-users"
TOKEN_TABLE_NAME="${PROJECT_NAME}-jedi-token-holocron"
TOKEN_SCAN_SCHEDULE="${PROJECT_NAME}-unused-token-check"
TOKEN_ALERT_TOPIC="${PROJECT_NAME}-auth-alerts"
TOKEN_ALERT_FILTER_NAME="${PROJECT_NAME}-unused-token-filter"
TOKEN_ALERT_ALARM_NAME="${PROJECT_NAME}-unused-token-alarm"
```

Load `.env`:

```bash
set -a
source "$ENV_FILE"
set +a
```

## 2. Look Up Generated IDs

If `.env` does not already contain generated IDs, look them up from AWS:

```bash
export HTTP_API_ID="${HTTP_API_ID:-$(aws apigatewayv2 get-apis \
  --query "Items[?Name=='${API_NAME}'].ApiId | [0]" \
  --output text \
  --region "$AWS_REGION")}"

export USER_POOL_ID="${USER_POOL_ID:-$(aws cognito-idp list-user-pools \
  --max-results 60 \
  --query "UserPools[?Name=='${USER_POOL_NAME}'].Id | [0]" \
  --output text \
  --region "$AWS_REGION")}"

export TOKEN_ALERT_TOPIC_ARN="${TOKEN_ALERT_TOPIC_ARN:-$(aws sns list-topics \
  --query "Topics[?ends_with(TopicArn, ':${TOKEN_ALERT_TOPIC}')].TopicArn | [0]" \
  --output text \
  --region "$AWS_REGION")}"
```

Confirm the active teardown values:

```bash
echo "$AWS_REGION"
echo "$PROJECT_NAME"
echo "${HTTP_API_ID}"
echo "$USER_POOL_ID"
echo "$TOKEN_ALERT_TOPIC_ARN"
echo "$TOKEN_TABLE_NAME"
echo "$TOKEN_DETECTOR_FUNCTION"
```

## 3. Delete Detector Alerting

```bash
aws scheduler delete-schedule \
  --name "$TOKEN_SCAN_SCHEDULE" \
  --group-name default \
  --region "$AWS_REGION"

aws cloudwatch delete-alarms \
  --alarm-names "$TOKEN_ALERT_ALARM_NAME" \
  --region "$AWS_REGION"

aws logs delete-metric-filter \
  --log-group-name "/aws/lambda/${TOKEN_DETECTOR_FUNCTION}" \
  --filter-name "$TOKEN_ALERT_FILTER_NAME" \
  --region "$AWS_REGION"

aws sns delete-topic \
  --topic-arn "$TOKEN_ALERT_TOPIC_ARN" \
  --region "$AWS_REGION"
```

## 4. Delete Lambda Functions

```bash
aws lambda delete-function \
  --function-name "$TOKEN_DETECTOR_FUNCTION" \
  --region "$AWS_REGION"

aws lambda delete-function \
  --function-name "$JEDI_FUNCTION" \
  --region "$AWS_REGION"

aws lambda delete-function \
  --function-name "$SITH_FUNCTION" \
  --region "$AWS_REGION"
```

## 5. Delete API Gateway, Cognito, And DynamoDB

```bash
aws apigatewayv2 delete-api \
  --api-id "$HTTP_API_ID" \
  --region "$AWS_REGION"

aws cognito-idp delete-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"

aws dynamodb delete-table \
  --table-name "$TOKEN_TABLE_NAME" \
  --region "$AWS_REGION"
```

## 6. Delete Log Groups

```bash
aws logs delete-log-group \
  --log-group-name "/aws/lambda/${TOKEN_DETECTOR_FUNCTION}" \
  --region "$AWS_REGION"

aws logs delete-log-group \
  --log-group-name "/aws/lambda/${JEDI_FUNCTION}" \
  --region "$AWS_REGION"

aws logs delete-log-group \
  --log-group-name "/aws/lambda/${SITH_FUNCTION}" \
  --region "$AWS_REGION"
```

## 7. Delete IAM Policy And Role

```bash
aws iam delete-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name "${PROJECT_NAME}-jedi-token-holocron-access"

aws iam detach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role \
  --role-name "$LAMBDA_ROLE_NAME"
```

## 8. Verify

```bash
aws apigatewayv2 get-apis --region "$AWS_REGION" \
  --query "Items[?Name=='${API_NAME}']"

aws lambda list-functions --region "$AWS_REGION" \
  --query "Functions[?starts_with(FunctionName, '${PROJECT_NAME}')]"

aws dynamodb list-tables --region "$AWS_REGION" \
  --query "TableNames[?@=='${TOKEN_TABLE_NAME}']"

aws cognito-idp list-user-pools --max-results 60 --region "$AWS_REGION" \
  --query "UserPools[?Name=='${USER_POOL_NAME}']"
```

## References

### AWS CLI Command References

Every AWS CLI command used in this teardown is linked below to the direct AWS command reference page.

| Command | AWS CLI reference |
| --- | --- |
| `aws apigatewayv2 get-apis` | [apigatewayv2 get-apis](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-apis.html) |
| `aws apigatewayv2 delete-api` | [apigatewayv2 delete-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/delete-api.html) |
| `aws cloudwatch delete-alarms` | [cloudwatch delete-alarms](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/delete-alarms.html) |
| `aws cognito-idp list-user-pools` | [cognito-idp list-user-pools](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/list-user-pools.html) |
| `aws cognito-idp delete-user-pool` | [cognito-idp delete-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/delete-user-pool.html) |
| `aws dynamodb delete-table` | [dynamodb delete-table](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/delete-table.html) |
| `aws dynamodb list-tables` | [dynamodb list-tables](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/list-tables.html) |
| `aws iam delete-role-policy` | [iam delete-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role-policy.html) |
| `aws iam detach-role-policy` | [iam detach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/detach-role-policy.html) |
| `aws iam delete-role` | [iam delete-role](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role.html) |
| `aws lambda delete-function` | [lambda delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html) |
| `aws lambda list-functions` | [lambda list-functions](https://docs.aws.amazon.com/cli/latest/reference/lambda/list-functions.html) |
| `aws logs delete-metric-filter` | [logs delete-metric-filter](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-metric-filter.html) |
| `aws logs delete-log-group` | [logs delete-log-group](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-log-group.html) |
| `aws scheduler delete-schedule` | [scheduler delete-schedule](https://docs.aws.amazon.com/cli/latest/reference/scheduler/delete-schedule.html) |
| `aws sns list-topics` | [sns list-topics](https://docs.aws.amazon.com/cli/latest/reference/sns/list-topics.html) |
| `aws sns delete-topic` | [sns delete-topic](https://docs.aws.amazon.com/cli/latest/reference/sns/delete-topic.html) |

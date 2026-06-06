# Token Detector REST Lab Teardown

## Purpose

Remove the token detector REST lab resources, then verify that add-on, identity, API, logging, alerting, and IAM lookups return deleted or empty results.

### Details

Task details:

- Load the environment values for the resources being removed
- Look up generated IDs when `.env` does not already contain them
- Delete application and API resources before dependent identity or IAM resources
- Delete token table, scanner schedule, metric filter, alarm, SNS topic, and detector Lambda resources
- Delete CloudWatch log groups and alarms after application resources are removed
- Verify that lookups return deleted, not-found, or empty results

## Prerequisites

### Dependencies

#### Applications

| Dependency | Requirement |
| --- | --- |
| AWS CLI | Delete resources and verify removed state. |
| jq | Parse lookup responses when generated IDs are missing from `.env`. |
| curl | Confirm public endpoints no longer respond when applicable. |

#### Infrastructure

| Dependency | Requirement |
| --- | --- |
| Existing REST resources | The resources named in `.env` were created by the matching runbook or lab. |
| Environment file | `.env` contains generated IDs, ARNs, names, and endpoints needed for deletion. |
| CloudWatch log groups | Log groups may outlive Lambda deletion and should be removed explicitly. |

#### Access Requirements

| Dependency | Requirement |
| --- | --- |
| AWS credentials | Use credentials with permission to delete API Gateway, Lambda, IAM, Cognito, CloudWatch, and related resources. |
| Account and region confirmation | Confirm the active account and region before running destructive commands. |

#### APIs And Services

| Dependency | Requirement |
| --- | --- |
| API Gateway | Delete REST or HTTP APIs, routes, integrations, stages, authorizers, and deployments. |
| Lambda and IAM | Delete functions, permissions, policies, and roles after dependent resources are removed. |
| Cognito | Delete user pools and app clients when they belong to this environment. |
| CloudWatch | Delete log groups, metric filters, and alarms created by the environment. |

### Supporting Files

| File | Use |
| --- | --- |
| [`../env.example`](../env.example) | Lab environment template showing token-detector values required by teardown. |
| [`../LAB-README.md`](../LAB-README.md) | Token detector lab document map. |
| [`deploy-token-detector-lab.md`](deploy-token-detector-lab.md) | Lab that creates the add-on resources removed here. |
| [`../sandbox/sandbox-info.md`](../sandbox/sandbox-info.md) | Sandbox note for locally edited lab files. |

> [!WARNING]
> These commands delete API Gateway, Lambda, Cognito, DynamoDB, EventBridge Scheduler, CloudWatch, SNS, and IAM resources. Confirm you are using the REST token-detector lab values before running teardown.


## 1. Create And Load The Environment File

An environment file helps simplify teardown and provides a record of planned values and resource outputs. Copy the dotenv template, rename the copy to `.env`, update the values for the environment you want to remove, then reload it before running commands that depend on those values.

Copy the template if `.env` does not already exist:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
export ENV_FILE="$REPO_ROOT/deploy-token-detector/labs/token-detector/.env"

cp "$REPO_ROOT/deploy-token-detector/labs/token-detector/env.example" "$ENV_FILE"
```

Open `.env` and confirm these values match the token-detector lab resources you want to remove:

```bash
code "$ENV_FILE"
```

```bash
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-rest"
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
export REST_API_ID="${REST_API_ID:-$(aws apigateway get-rest-apis \
  --query "items[?name=='${API_NAME}'].id | [0]" \
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
echo "${REST_API_ID}"
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
aws apigateway delete-rest-api \
  --rest-api-id "$REST_API_ID" \
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
aws apigateway get-rest-apis --region "$AWS_REGION" \
  --query "items[?name=='${API_NAME}']"

aws lambda list-functions --region "$AWS_REGION" \
  --query "Functions[?starts_with(FunctionName, '${PROJECT_NAME}')]"

aws dynamodb list-tables --region "$AWS_REGION" \
  --query "TableNames[?@=='${TOKEN_TABLE_NAME}']"

aws cognito-idp list-user-pools --max-results 60 --region "$AWS_REGION" \
  --query "UserPools[?Name=='${USER_POOL_NAME}']"
```

## References

| Topic | References |
| --- | --- |
| DynamoDB token table cleanup | [Working with DynamoDB items](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html), [DynamoDB Time to Live](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html) |
| Lambda detector cleanup | [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), [Lambda execution roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html), [Lambda environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html) |
| CloudWatch alarm and metric cleanup | [CloudWatch Logs metric filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html), [Filter pattern syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html), [CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) |
| Notification and scheduled workflow cleanup | [Amazon SNS email notifications](https://docs.aws.amazon.com/sns/latest/dg/sns-email-notifications.html), [EventBridge scheduled rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html), [EventBridge Scheduler user guide](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html) |

## CLI Command References

### AWS CLI References

| Command | AWS CLI reference |
| --- | --- |
| `aws apigateway get-rest-apis` | [apigateway get-rest-apis](https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-rest-apis.html) |
| `aws cognito-idp list-user-pools` | [cognito-idp list-user-pools](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/list-user-pools.html) |
| `aws sns list-topics` | [sns list-topics](https://docs.aws.amazon.com/cli/latest/reference/sns/list-topics.html) |
| `aws scheduler delete-schedule` | [scheduler delete-schedule](https://docs.aws.amazon.com/cli/latest/reference/scheduler/delete-schedule.html) |
| `aws cloudwatch delete-alarms` | [cloudwatch delete-alarms](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/delete-alarms.html) |
| `aws logs delete-metric-filter` | [logs delete-metric-filter](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-metric-filter.html) |
| `aws sns delete-topic` | [sns delete-topic](https://docs.aws.amazon.com/cli/latest/reference/sns/delete-topic.html) |
| `aws lambda delete-function` | [lambda delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html) |
| `aws apigateway delete-rest-api` | [apigateway delete-rest-api](https://docs.aws.amazon.com/cli/latest/reference/apigateway/delete-rest-api.html) |
| `aws cognito-idp delete-user-pool` | [cognito-idp delete-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/delete-user-pool.html) |
| `aws dynamodb delete-table` | [dynamodb delete-table](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/delete-table.html) |
| `aws logs delete-log-group` | [logs delete-log-group](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-log-group.html) |
| `aws iam delete-role-policy` | [iam delete-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role-policy.html) |
| `aws iam detach-role-policy` | [iam detach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/detach-role-policy.html) |
| `aws iam delete-role` | [iam delete-role](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role.html) |
| `aws lambda list-functions` | [lambda list-functions](https://docs.aws.amazon.com/cli/latest/reference/lambda/list-functions.html) |
| `aws dynamodb list-tables` | [dynamodb list-tables](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/list-tables.html) |

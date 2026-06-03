# Unused Token Detector Lab HTTPS Teardown

Use this to tear down an HTTPS/HTTP API version of the unused-token detector lab. This removes the base HTTPS lab plus detector resources.

> [!NOTE]
> These commands match the detector deployment teardown. Skip any command for a resource you did not create.

## Commands

See the production detector HTTPS teardown:

```bash
less ../../../deploy-token-detector/docs/TEARDOWN_HTTPS.md
```

Quick command set:

```bash
export AWS_REGION="us-east-1"
export PROJECT_NAME="chewbacca-auth-http"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export TOKEN_DETECTOR_FUNCTION="${PROJECT_NAME}-unused-token-detector"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"
export API_NAME="${PROJECT_NAME}-api"
export USER_POOL_NAME="${PROJECT_NAME}-users"
export TOKEN_TABLE_NAME="${PROJECT_NAME}-jedi-token-holocron"
export TOKEN_SCAN_SCHEDULE="${PROJECT_NAME}-unused-token-check"
export TOKEN_ALERT_TOPIC="${PROJECT_NAME}-auth-alerts"
export TOKEN_ALERT_FILTER_NAME="${PROJECT_NAME}-unused-token-filter"
export TOKEN_ALERT_ALARM_NAME="${PROJECT_NAME}-unused-token-alarm"

export HTTP_API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='${API_NAME}'].ApiId | [0]" --output text --region "$AWS_REGION")
export USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 60 --query "UserPools[?Name=='${USER_POOL_NAME}'].Id | [0]" --output text --region "$AWS_REGION")
export TOKEN_ALERT_TOPIC_ARN=$(aws sns list-topics --query "Topics[?ends_with(TopicArn, ':${TOKEN_ALERT_TOPIC}')].TopicArn | [0]" --output text --region "$AWS_REGION")
```

```bash
aws scheduler delete-schedule --name "$TOKEN_SCAN_SCHEDULE" --group-name default --region "$AWS_REGION"
aws cloudwatch delete-alarms --alarm-names "$TOKEN_ALERT_ALARM_NAME" --region "$AWS_REGION"
aws logs delete-metric-filter --log-group-name "/aws/lambda/${TOKEN_DETECTOR_FUNCTION}" --filter-name "$TOKEN_ALERT_FILTER_NAME" --region "$AWS_REGION"
aws sns delete-topic --topic-arn "$TOKEN_ALERT_TOPIC_ARN" --region "$AWS_REGION"

aws lambda delete-function --function-name "$TOKEN_DETECTOR_FUNCTION" --region "$AWS_REGION"
aws lambda delete-function --function-name "$JEDI_FUNCTION" --region "$AWS_REGION"
aws lambda delete-function --function-name "$SITH_FUNCTION" --region "$AWS_REGION"

aws apigatewayv2 delete-api --api-id "$HTTP_API_ID" --region "$AWS_REGION"
aws cognito-idp delete-user-pool --user-pool-id "$USER_POOL_ID" --region "$AWS_REGION"
aws dynamodb delete-table --table-name "$TOKEN_TABLE_NAME" --region "$AWS_REGION"

aws logs delete-log-group --log-group-name "/aws/lambda/${TOKEN_DETECTOR_FUNCTION}" --region "$AWS_REGION"
aws logs delete-log-group --log-group-name "/aws/lambda/${JEDI_FUNCTION}" --region "$AWS_REGION"
aws logs delete-log-group --log-group-name "/aws/lambda/${SITH_FUNCTION}" --region "$AWS_REGION"

aws iam delete-role-policy --role-name "$LAMBDA_ROLE_NAME" --policy-name "${PROJECT_NAME}-jedi-token-holocron-access"
aws iam detach-role-policy --role-name "$LAMBDA_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name "$LAMBDA_ROLE_NAME"
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
| `aws iam delete-role-policy` | [iam delete-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role-policy.html) |
| `aws iam detach-role-policy` | [iam detach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/detach-role-policy.html) |
| `aws iam delete-role` | [iam delete-role](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role.html) |
| `aws lambda delete-function` | [lambda delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html) |
| `aws logs delete-metric-filter` | [logs delete-metric-filter](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-metric-filter.html) |
| `aws logs delete-log-group` | [logs delete-log-group](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-log-group.html) |
| `aws scheduler delete-schedule` | [scheduler delete-schedule](https://docs.aws.amazon.com/cli/latest/reference/scheduler/delete-schedule.html) |
| `aws sns list-topics` | [sns list-topics](https://docs.aws.amazon.com/cli/latest/reference/sns/list-topics.html) |
| `aws sns delete-topic` | [sns delete-topic](https://docs.aws.amazon.com/cli/latest/reference/sns/delete-topic.html) |

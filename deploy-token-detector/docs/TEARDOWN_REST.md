# Token Detector REST Teardown

Use this to tear down the REST Cognito auth infrastructure plus the unused-token detector add-on. Skip any command for a resource you did not create.

## 1. Export Values

```bash
export AWS_REGION="us-east-1"
export PROJECT_NAME="chewbacca-auth-rest"

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
```

## 2. Look Up Generated IDs

```bash
export REST_API_ID=$(aws apigateway get-rest-apis \
  --query "items[?name=='${API_NAME}'].id | [0]" \
  --output text \
  --region "$AWS_REGION")

export USER_POOL_ID=$(aws cognito-idp list-user-pools \
  --max-results 60 \
  --query "UserPools[?Name=='${USER_POOL_NAME}'].Id | [0]" \
  --output text \
  --region "$AWS_REGION")

export TOKEN_ALERT_TOPIC_ARN=$(aws sns list-topics \
  --query "Topics[?ends_with(TopicArn, ':${TOKEN_ALERT_TOPIC}')].TopicArn | [0]" \
  --output text \
  --region "$AWS_REGION")
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

## 5. Delete REST API, Cognito, And DynamoDB

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

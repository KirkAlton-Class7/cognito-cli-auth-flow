# REST Lab Teardown

Use this to tear down the base REST Cognito auth infrastructure. It does not remove token-detector resources.

> [!WARNING]
> These commands delete the REST API, Lambda functions, Cognito user pool, CloudWatch log groups, and IAM role. Confirm you are using the REST values before running teardown.

## 1. Export Values

```bash
export AWS_REGION="us-east-1"
export PROJECT_NAME="chewbacca-auth-rest"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"

export API_NAME="${PROJECT_NAME}-api"
export USER_POOL_NAME="${PROJECT_NAME}-users"
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
```

Confirm the active teardown values:

```bash
echo "$AWS_REGION"
echo "$PROJECT_NAME"
echo "$REST_API_ID"
echo "$USER_POOL_ID"
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
echo "$LAMBDA_ROLE_NAME"
```

## 3. Delete Base REST Resources

Delete the REST API. This removes its resources, methods, integrations, deployments, stages, and Cognito authorizer:

```bash
aws apigateway delete-rest-api \
  --rest-api-id "$REST_API_ID" \
  --region "$AWS_REGION"
```

Delete the Lambda functions:

```bash
aws lambda delete-function \
  --function-name "$JEDI_FUNCTION" \
  --region "$AWS_REGION"

aws lambda delete-function \
  --function-name "$SITH_FUNCTION" \
  --region "$AWS_REGION"
```

Delete the Cognito user pool. This also removes the app client, test user, MFA configuration, and issued-token context:

```bash
aws cognito-idp delete-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"
```

## 4. Delete Log Groups

```bash
aws logs delete-log-group \
  --log-group-name "/aws/lambda/${JEDI_FUNCTION}" \
  --region "$AWS_REGION"

aws logs delete-log-group \
  --log-group-name "/aws/lambda/${SITH_FUNCTION}" \
  --region "$AWS_REGION"
```

## 5. Delete IAM Role

```bash
aws iam detach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role \
  --role-name "$LAMBDA_ROLE_NAME"
```

## 6. Verify

The REST API deletion removes resources, methods, integrations, deployments, stages, and the authorizer. Validate the API itself, then validate each standalone resource that was created outside the API container.

```bash
aws apigateway get-rest-api \
  --rest-api-id "$REST_API_ID" \
  --region "$AWS_REGION"

aws cognito-idp describe-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"

aws lambda get-function \
  --function-name "$JEDI_FUNCTION" \
  --region "$AWS_REGION"

aws lambda get-function \
  --function-name "$SITH_FUNCTION" \
  --region "$AWS_REGION"

aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/${JEDI_FUNCTION}" \
  --region "$AWS_REGION"

aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/${SITH_FUNCTION}" \
  --region "$AWS_REGION"

aws iam get-role \
  --role-name "$LAMBDA_ROLE_NAME"
```

Expected result:

- REST API, Cognito user pool, Lambda functions, and IAM role checks should return not-found style errors.
- CloudWatch log group checks should return an empty `logGroups` list for each Lambda function.

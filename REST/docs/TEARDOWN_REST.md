# REST Teardown

Use this to tear down the base REST Cognito auth deployment. It does not remove token-detector resources.

> [!WARNING]
> These commands delete the REST API, Lambda functions, Cognito user pool, CloudWatch log groups, and IAM roles. Confirm you are using the REST values before running teardown.

## 1. Create And Load The Environment File

An environment file helps simplify teardown and provides a record of planned values and resource outputs. Copy the dotenv template, rename the copy to `.env`, update the values for the environment you want to remove, then reload it before running commands that depend on those values.

Copy the template if `.env` does not already exist:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
export ENV_FILE="$REPO_ROOT/REST/.env"

cp "$REPO_ROOT/REST/env.example" "$ENV_FILE"
```

Open `.env` and confirm these values match the REST resources you want to remove:

```bash
code "$ENV_FILE"
```

```bash
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-rest"
JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
SITH_FUNCTION="${PROJECT_NAME}-sith-node"
PYTHON_LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-python-role"
NODE_LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-node-role"
API_NAME="${PROJECT_NAME}-api"
USER_POOL_NAME="${PROJECT_NAME}-users"
REST_API_ID=""
USER_POOL_ID=""
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
```

Confirm the active teardown values:

```bash
echo "$AWS_REGION"
echo "$PROJECT_NAME"
echo "${REST_API_ID}"
echo "$USER_POOL_ID"
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
echo "$PYTHON_LAMBDA_ROLE_NAME"
echo "$NODE_LAMBDA_ROLE_NAME"
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

## 5. Delete IAM Roles

```bash
aws iam detach-role-policy \
  --role-name "$PYTHON_LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role \
  --role-name "$PYTHON_LAMBDA_ROLE_NAME"

aws iam detach-role-policy \
  --role-name "$NODE_LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role \
  --role-name "$NODE_LAMBDA_ROLE_NAME"
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
  --role-name "$PYTHON_LAMBDA_ROLE_NAME"

aws iam get-role \
  --role-name "$NODE_LAMBDA_ROLE_NAME"
```

Expected result:

- API Gateway, Cognito user pool, Lambda functions, and IAM role checks should return not-found style errors.
- CloudWatch log group checks should return an empty `logGroups` list for each Lambda function.

## References

### AWS CLI Command References

Every AWS CLI command used in this teardown is linked below to the direct AWS command reference page.

| Command | AWS CLI reference |
| --- | --- |
| `aws apigateway get-rest-apis` | [apigateway get-rest-apis](https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-rest-apis.html) |
| `aws apigateway delete-rest-api` | [apigateway delete-rest-api](https://docs.aws.amazon.com/cli/latest/reference/apigateway/delete-rest-api.html) |
| `aws apigateway get-rest-api` | [apigateway get-rest-api](https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-rest-api.html) |
| `aws cognito-idp list-user-pools` | [cognito-idp list-user-pools](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/list-user-pools.html) |
| `aws cognito-idp delete-user-pool` | [cognito-idp delete-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/delete-user-pool.html) |
| `aws cognito-idp describe-user-pool` | [cognito-idp describe-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/describe-user-pool.html) |
| `aws lambda delete-function` | [lambda delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html) |
| `aws lambda get-function` | [lambda get-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function.html) |
| `aws logs delete-log-group` | [logs delete-log-group](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-log-group.html) |
| `aws logs describe-log-groups` | [logs describe-log-groups](https://docs.aws.amazon.com/cli/latest/reference/logs/describe-log-groups.html) |
| `aws iam detach-role-policy` | [iam detach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/detach-role-policy.html) |
| `aws iam delete-role` | [iam delete-role](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |

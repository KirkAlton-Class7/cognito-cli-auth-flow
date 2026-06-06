# HTTPS Teardown

## Purpose

Remove the Cognito auth flow HTTPS deployment resources, then verify that API, Lambda, Cognito, CloudWatch, and IAM lookups return deleted or empty results.

### Details

Task details:

- Load the environment values for the resources being removed
- Look up generated IDs when `.env` does not already contain them
- Delete application and API resources before dependent identity or IAM resources
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
| Existing HTTPS resources | The resources named in `.env` were created by the matching runbook or lab. |
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
| [`../env.example`](../env.example) | Environment template showing HTTPS values required by teardown. |
| [`../README.md`](../README.md) | HTTPS deployment document map. |
| [`RUNBOOK-CLI.md`](RUNBOOK-CLI.md) | CLI runbook that creates the resources removed here. |
| [`RUNBOOK-CONSOLE.md`](RUNBOOK-CONSOLE.md) | Console runbook that creates the resources removed here. |

> [!WARNING]
> These commands delete the HTTP API, Lambda functions, Cognito user pool, CloudWatch log groups, and IAM roles. Confirm you are using the HTTPS values before running teardown.


## 1. Create And Load The Environment File

An environment file helps simplify teardown and provides a record of planned values and resource outputs. Copy the dotenv template, rename the copy to `.env`, update the values for the environment you want to remove, then reload it before running commands that depend on those values.

Copy the template if `.env` does not already exist:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
export ENV_FILE="$REPO_ROOT/HTTPS/.env"

cp "$REPO_ROOT/HTTPS/env.example" "$ENV_FILE"
```

Open `.env` and confirm these values match the HTTPS resources you want to remove:

```bash
code "$ENV_FILE"
```

```bash
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-http"
JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
SITH_FUNCTION="${PROJECT_NAME}-sith-node"
PYTHON_LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-python-role"
NODE_LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-node-role"
API_NAME="${PROJECT_NAME}-api"
USER_POOL_NAME="${PROJECT_NAME}-users"
API_ID=""
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
export HTTP_API_ID="${API_ID:-$(aws apigatewayv2 get-apis \
  --query "Items[?Name=='${API_NAME}'].ApiId | [0]" \
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
echo "${HTTP_API_ID}"
echo "$USER_POOL_ID"
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
echo "$PYTHON_LAMBDA_ROLE_NAME"
echo "$NODE_LAMBDA_ROLE_NAME"
```

## 3. Delete Base HTTPS Resources

Delete the HTTP API. This removes its routes, integrations, stages, and authorizer:

```bash
aws apigatewayv2 delete-api \
  --api-id "$HTTP_API_ID" \
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

The HTTP API deletion removes routes, integrations, stages, and the authorizer. Validate the API itself, then validate each standalone resource that was created outside the API container.

```bash
aws apigatewayv2 get-api \
  --api-id "$HTTP_API_ID" \
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

| Topic | References |
| --- | --- |
| Cognito identity resources to remove | [Cognito User Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html), [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html), [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html), [Managed login and hosted UI](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-hosted-ui-user-experience.html) |
| HTTP API resources to remove | [API Gateway HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html), [HTTP API routes](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-routes.html), [HTTP API stages](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-stages.html), [HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html), [HTTP API Lambda integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html) |
| Lambda functions, permissions, and roles to remove | [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), [Invoking Lambda with API Gateway](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html), [Lambda execution roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html) |
| CloudWatch evidence to clean up | [CloudWatch Logs for Lambda](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html) |

## CLI Command References

### AWS CLI References

| Command | AWS CLI reference |
| --- | --- |
| `aws apigatewayv2 get-apis` | [apigatewayv2 get-apis](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-apis.html) |
| `aws cognito-idp list-user-pools` | [cognito-idp list-user-pools](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/list-user-pools.html) |
| `aws apigatewayv2 delete-api` | [apigatewayv2 delete-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/delete-api.html) |
| `aws lambda delete-function` | [lambda delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html) |
| `aws cognito-idp delete-user-pool` | [cognito-idp delete-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/delete-user-pool.html) |
| `aws logs delete-log-group` | [logs delete-log-group](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-log-group.html) |
| `aws iam detach-role-policy` | [iam detach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/detach-role-policy.html) |
| `aws iam delete-role` | [iam delete-role](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role.html) |
| `aws apigatewayv2 get-api` | [apigatewayv2 get-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-api.html) |
| `aws cognito-idp describe-user-pool` | [cognito-idp describe-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/describe-user-pool.html) |
| `aws lambda get-function` | [lambda get-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function.html) |
| `aws logs describe-log-groups` | [logs describe-log-groups](https://docs.aws.amazon.com/cli/latest/reference/logs/describe-log-groups.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |

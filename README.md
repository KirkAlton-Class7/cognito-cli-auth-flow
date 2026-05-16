---
title: Chewbacca Cognito CLI Auth Flow Lab
description: Basic AWS CLI walkthrough for Cognito USER_AUTH, challenge selection, MFA, JWT validation, API Gateway, and Lambda using a Chewbacca, Jedi, and Sith theme.
created: 2026-05-16
updated: 2026-05-16
tags:
  - aws
  - cognito
  - lambda
  - api-gateway
  - jwt
  - auth-flow
type: runbook
status: active
---

# Chewbacca Cognito CLI Auth Flow Lab

This lab rebuilds the class workflow that shows how Cognito authentication works from the command line. It keeps the architecture intentionally small: one user pool, one app client, two Lambda functions, one HTTP API, and a Cognito JWT authorizer.


## What You Build

```text
CLI user
  -> Cognito User Pool
  -> USER_AUTH / SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> JWT tokens
  -> API Gateway HTTP API
  -> Cognito JWT Authorizer
  -> Lambda
  -> CloudWatch Logs
```

The point is not to build a full application. The point is to see each authentication step clearly.

The API routes are intentionally simple:

| Route | Runtime | Theme role |
| --- | --- | --- |
| `/prod/jedi` | Python | Jedi Council response path |
| `/prod/sith` | Node.js | Sith response path |

## Source Material

| Source | Purpose |
| --- | --- |
| `/Users/kirk/Codex/sandbox/cognito-class7-05-05-2026.md` | Recovered class notes for `USER_AUTH`, challenge selection, MFA, and token handling |
| `/Users/kirk/Codex/sandbox/lambda/lessonb` | Simple API Gateway + Lambda lab pattern |
| `/Users/kirk/Codex/sandbox/cognito-cli-auth-flow/lambda` | Simplified Chewbacca/Jedi/Sith Lambda functions for this runbook |
| `/Users/kirk/Codex/sandbox/cognito-cli-auth-flow/scripts/secret_hash.py` | Helper script for Cognito app clients with a client secret |

## Prerequisites

Install or confirm these tools:

```bash
aws --version
jq --version
python3 --version
zip --version
```

Confirm your AWS identity:

```bash
aws sts get-caller-identity
```

Set the working directory:

```bash
cd /Users/kirk/Codex/sandbox/cognito-cli-auth-flow
```

## 1. Export Lab Variables

Use one region for the full lab.

```bash
export AWS_REGION="us-east-1"
export PROJECT_NAME="chewbacca-auth"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"

export API_NAME="${PROJECT_NAME}-http-api"
export USER_POOL_NAME="${PROJECT_NAME}-users"
export USER_POOL_CLIENT_NAME="${PROJECT_NAME}-cli-client"
export AUTHORIZER_NAME="${PROJECT_NAME}-cognito-jwt"

export TEST_USERNAME="chewbacca"
export TEST_EMAIL="chewbacca@example.com"
export TEST_PASSWORD="Wookiee#2026!"
```

Get your AWS account ID:

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

Validation:

```bash
echo "$AWS_REGION"
echo "$AWS_ACCOUNT_ID"
echo "$PROJECT_NAME"
```

## 2. Create the Lambda Execution Role

Lambda needs permission to write logs to CloudWatch.

```bash
aws iam create-role \
  --role-name "$LAMBDA_ROLE_NAME" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'
```

Attach the basic execution policy:

```bash
aws iam attach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Export the role ARN:

```bash
export LAMBDA_ROLE_ARN=$(aws iam get-role \
  --role-name "$LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text)
```

Give IAM a few seconds to propagate:

```bash
sleep 10
```

Validation:

```bash
echo "$LAMBDA_ROLE_ARN"
```

## 3. Package the Lambda Functions

Package the provided Jedi and Sith functions.

```bash
cd /Users/kirk/Codex/sandbox/cognito-cli-auth-flow/lambda

zip jedi-python.zip jedi_python.py
zip sith-node.zip sith_node.js
```

Validation:

```bash
ls -lh *.zip
```

## 4. Create the Lambda Functions

Create the Jedi Python Lambda:

```bash
aws lambda create-function \
  --function-name "$JEDI_FUNCTION" \
  --runtime python3.12 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler jedi_python.lambda_handler \
  --zip-file fileb://jedi-python.zip \
  --region "$AWS_REGION"
```

Create the Sith Node.js Lambda:

```bash
aws lambda create-function \
  --function-name "$SITH_FUNCTION" \
  --runtime nodejs20.x \
  --role "$LAMBDA_ROLE_ARN" \
  --handler sith_node.handler \
  --zip-file fileb://sith-node.zip \
  --region "$AWS_REGION"
```

Export function ARNs:

```bash
export JEDI_FUNCTION_ARN=$(aws lambda get-function \
  --function-name "$JEDI_FUNCTION" \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region "$AWS_REGION")

export SITH_FUNCTION_ARN=$(aws lambda get-function \
  --function-name "$SITH_FUNCTION" \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region "$AWS_REGION")
```

Validation:

```bash
echo "$JEDI_FUNCTION_ARN"
echo "$SITH_FUNCTION_ARN"
```

## 5. Test Lambda Directly

Invoke the Jedi Python function:

```bash
aws lambda invoke \
  --function-name "$JEDI_FUNCTION" \
  --payload '{"queryStringParameters":{"name":"Chewbacca"}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/chewbacca-jedi-response.json \
  --region "$AWS_REGION"

jq . /tmp/chewbacca-jedi-response.json
```

Invoke the Sith Node.js function:

```bash
aws lambda invoke \
  --function-name "$SITH_FUNCTION" \
  --payload '{"queryStringParameters":{"name":"Chewbacca"}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/chewbacca-sith-response.json \
  --region "$AWS_REGION"

jq . /tmp/chewbacca-sith-response.json
```

Validation:

- Jedi Python returns a JSON body with `The Python Jedi Council accepts your request.`
- Sith Node returns a JSON body with `THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.`
- CloudWatch has log groups for both functions.

## 6. Create the HTTP API

Create the API:

```bash
export API_ID=$(aws apigatewayv2 create-api \
  --name "$API_NAME" \
  --protocol-type HTTP \
  --query 'ApiId' \
  --output text \
  --region "$AWS_REGION")
```

Export the endpoint:

```bash
export API_ENDPOINT=$(aws apigatewayv2 get-api \
  --api-id "$API_ID" \
  --query 'ApiEndpoint' \
  --output text \
  --region "$AWS_REGION")
```

Validation:

```bash
echo "$API_ID"
echo "$API_ENDPOINT"
```

## 7. Add Lambda Integrations

Create the Jedi integration:

```bash
export JEDI_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "$API_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${JEDI_FUNCTION_ARN}/invocations" \
  --payload-format-version "2.0" \
  --query 'IntegrationId' \
  --output text \
  --region "$AWS_REGION")
```

Create the Sith integration:

```bash
export SITH_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "$API_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${SITH_FUNCTION_ARN}/invocations" \
  --payload-format-version "2.0" \
  --query 'IntegrationId' \
  --output text \
  --region "$AWS_REGION")
```

Create routes:

```bash
aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key "GET /jedi" \
  --target "integrations/$JEDI_INTEGRATION_ID" \
  --region "$AWS_REGION"

aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key "GET /sith" \
  --target "integrations/$SITH_INTEGRATION_ID" \
  --region "$AWS_REGION"
```

Create the `prod` stage:

```bash
aws apigatewayv2 create-stage \
  --api-id "$API_ID" \
  --stage-name prod \
  --auto-deploy \
  --region "$AWS_REGION"
```

Allow API Gateway to invoke Lambda:

```bash
aws lambda add-permission \
  --function-name "$JEDI_FUNCTION" \
  --statement-id "${API_ID}-jedi-invoke" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/jedi" \
  --region "$AWS_REGION"

aws lambda add-permission \
  --function-name "$SITH_FUNCTION" \
  --statement-id "${API_ID}-sith-invoke" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/sith" \
  --region "$AWS_REGION"
```

## 8. Test the Public API Before Auth

Before adding Cognito, prove routing works.

```bash
curl "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
curl "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show API Gateway event payloads.
- The event shape is different from the direct Lambda test payload.

## 9. Create the Cognito User Pool

Create a user pool with optional software token MFA.

```bash
export USER_POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "$USER_POOL_NAME" \
  --mfa-configuration OPTIONAL \
  --software-token-mfa-configuration Enabled=true \
  --alias-attributes email \
  --auto-verified-attributes email \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 12,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true
    }
  }' \
  --query 'UserPool.Id' \
  --output text \
  --region "$AWS_REGION")
```

Export the issuer URL:

```bash
export COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"
```

Validation:

```bash
echo "$USER_POOL_ID"
echo "$COGNITO_ISSUER"
```

## 10. Create the App Client

This lab uses an app client with a client secret on purpose so you can learn `SECRET_HASH`.

```bash
export CLIENT_JSON=$(aws cognito-idp create-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-name "$USER_POOL_CLIENT_NAME" \
  --generate-secret \
  --explicit-auth-flows ALLOW_USER_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query 'UserPoolClient' \
  --output json \
  --region "$AWS_REGION")
```

Export client values:

```bash
export CLIENT_ID=$(echo "$CLIENT_JSON" | jq -r '.ClientId')
export CLIENT_SECRET=$(echo "$CLIENT_JSON" | jq -r '.ClientSecret')
```

Validation:

```bash
echo "$CLIENT_ID"
echo "${CLIENT_SECRET:0:8}..."
```

> [!IMPORTANT]
> Do not commit real Cognito client secrets. This lab prints only a short prefix for validation.

## 11. Create the Test User

Create `chewbacca` and suppress the welcome email:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEST_USERNAME" \
  --temporary-password "$TEST_PASSWORD" \
  --user-attributes Name=email,Value="$TEST_EMAIL" Name=email_verified,Value=true \
  --message-action SUPPRESS \
  --region "$AWS_REGION"
```

Set the password as permanent:

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEST_USERNAME" \
  --password "$TEST_PASSWORD" \
  --permanent \
  --region "$AWS_REGION"
```

Validation:

```bash
aws cognito-idp admin-get-user \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEST_USERNAME" \
  --region "$AWS_REGION" \
  --query '{Username:Username,Status:UserStatus,Enabled:Enabled}'
```

## 12. Generate the Cognito SECRET_HASH

`SECRET_HASH` proves the request knows the app client secret without sending the raw secret as the challenge answer.

```bash
cd /Users/kirk/Codex/sandbox/cognito-cli-auth-flow

export SECRET_HASH=$(python3 scripts/secret_hash.py \
  "$TEST_USERNAME" \
  "$CLIENT_ID" \
  "$CLIENT_SECRET")
```

Validation:

```bash
echo "${SECRET_HASH:0:20}"
```

## 13. Bootstrap Chewbacca TOTP MFA

First authenticate with the direct password flow. MFA is optional right now, so Cognito should return tokens.

```bash
export INITIAL_AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")
```

Export the temporary access token:

```bash
export ACCESS_TOKEN=$(echo "$INITIAL_AUTH_RESPONSE" | jq -r '.AuthenticationResult.AccessToken')
```

Ask Cognito for a software token secret:

```bash
export TOTP_SETUP_RESPONSE=$(aws cognito-idp associate-software-token \
  --access-token "$ACCESS_TOKEN" \
  --region "$AWS_REGION")
```

Print the secret code:

```bash
export TOTP_SECRET=$(echo "$TOTP_SETUP_RESPONSE" | jq -r '.SecretCode')
echo "$TOTP_SECRET"
```

Add that secret to an authenticator app as a manual setup key.

Then export the current six-digit code:

```bash
export TOTP_CODE="123456"
```

Verify the software token:

```bash
aws cognito-idp verify-software-token \
  --access-token "$ACCESS_TOKEN" \
  --user-code "$TOTP_CODE" \
  --friendly-device-name "Chewbacca CLI" \
  --region "$AWS_REGION"
```

Set software token MFA as the preferred MFA method:

```bash
aws cognito-idp set-user-mfa-preference \
  --access-token "$ACCESS_TOKEN" \
  --software-token-mfa-settings Enabled=true,PreferredMfa=true \
  --region "$AWS_REGION"
```

Validation:

- The authenticator app is enrolled.
- `chewbacca` now has software token MFA enabled.
- Future password auth should return `SOFTWARE_TOKEN_MFA` before issuing tokens.

## 14. Run the USER_AUTH Negotiated Flow

This is the class workflow you were looking for.

`USER_AUTH` starts with negotiation. Cognito asks which challenge you want to use.

```bash
export AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")
```

Inspect the response:

```bash
echo "$AUTH_RESPONSE" | jq
```

Expected shape:

```json
{
  "ChallengeName": "SELECT_CHALLENGE",
  "AvailableChallenges": [
    "PASSWORD",
    "PASSWORD_SRP"
  ],
  "Session": "..."
}
```

Export the session:

```bash
export SESSION=$(echo "$AUTH_RESPONSE" | jq -r '.Session')
echo "${SESSION:0:20}"
```

## 15. Choose the PASSWORD Challenge

This is the `choose challenge` step.

```bash
export PASSWORD_CHALLENGE_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="$TEST_USERNAME",ANSWER="PASSWORD",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")
```

Inspect the response:

```bash
echo "$PASSWORD_CHALLENGE_RESPONSE" | jq
```

Expected shape:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "..."
}
```

Export the new session:

```bash
export SESSION=$(echo "$PASSWORD_CHALLENGE_RESPONSE" | jq -r '.Session')
```

## 16. Respond to the SOFTWARE_TOKEN_MFA Challenge

Get a fresh code from the authenticator app:

```bash
export TOTP_CODE="123456"
```

Respond to the MFA challenge:

```bash
export MFA_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="$TEST_USERNAME",SOFTWARE_TOKEN_MFA_CODE="$TOTP_CODE",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")
```

Export tokens:

```bash
export ACCESS_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.AccessToken')
export ID_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.IdToken')
export REFRESH_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.RefreshToken')
```

Validation:

```bash
echo "${ACCESS_TOKEN:0:24}"
echo "${ID_TOKEN:0:24}"
echo "${REFRESH_TOKEN:0:24}"
```

## 17. Token Use

| Token | What it represents | Use in this lab |
| --- | --- | --- |
| Access token | Permission to call APIs | Use with API Gateway JWT authorizer |
| ID token | User identity/profile claims | Useful for inspecting user identity |
| Refresh token | Used to request new tokens | Keep private; do not send to API Gateway |

For API testing, use:

```bash
Authorization: Bearer $ACCESS_TOKEN
```

## 18. Add the Cognito JWT Authorizer

Create the HTTP API JWT authorizer:

```bash
export COGNITO_AUTHORIZER_ID=$(aws apigatewayv2 create-authorizer \
  --api-id "$API_ID" \
  --name "$AUTHORIZER_NAME" \
  --authorizer-type JWT \
  --identity-source '$request.header.Authorization' \
  --jwt-configuration "{\"Audience\":[\"${CLIENT_ID}\"],\"Issuer\":\"${COGNITO_ISSUER}\"}" \
  --query 'AuthorizerId' \
  --output text \
  --region "$AWS_REGION")
```

Export route IDs:

```bash
export JEDI_ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "$API_ID" \
  --query "Items[?RouteKey=='GET /jedi'].RouteId | [0]" \
  --output text \
  --region "$AWS_REGION")

export SITH_ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "$API_ID" \
  --query "Items[?RouteKey=='GET /sith'].RouteId | [0]" \
  --output text \
  --region "$AWS_REGION")
```

Attach the authorizer to both routes:

```bash
aws apigatewayv2 update-route \
  --api-id "$API_ID" \
  --route-id "$JEDI_ROUTE_ID" \
  --authorization-type JWT \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"

aws apigatewayv2 update-route \
  --api-id "$API_ID" \
  --route-id "$SITH_ROUTE_ID" \
  --authorization-type JWT \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

Validation:

```bash
aws apigatewayv2 get-authorizer \
  --api-id "$API_ID" \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

## 19. Test Protected API Routes

Test without a token:

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected:

```text
HTTP/2 401
```

Test with the Cognito access token:

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Test the Sith route:

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Validation:

- Missing token returns `401`.
- Valid token returns `200`.
- Lambda logs appear only when authorization succeeds.

## 20. Direct Flow Shortcut

After MFA is enabled, `USER_PASSWORD_AUTH` skips `SELECT_CHALLENGE` and goes straight to password validation, then MFA.

```bash
export DIRECT_AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")
```

Expected:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "..."
}
```

This is simpler for CLI testing, but it does not teach the `SELECT_CHALLENGE` negotiation step.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unable to verify secret hash` | Wrong username, client ID, client secret, or copied hash | Regenerate `SECRET_HASH` with the exact same username used in the auth request |
| `InvalidParameterException` for `USER_AUTH` | App client does not allow `ALLOW_USER_AUTH` or region/account does not support choice-based auth | Recreate/update app client with `ALLOW_USER_AUTH`; use `USER_PASSWORD_AUTH` if unavailable |
| `NotAuthorizedException` | Wrong password, stale session, wrong secret hash, or expired MFA step | Start the flow again from `initiate-auth` |
| `CodeMismatchException` | MFA code expired or copied incorrectly | Wait for a fresh authenticator code |
| API returns `401` | Missing token, expired token, wrong issuer, wrong audience/client ID | Re-run the MFA flow and export a fresh `ACCESS_TOKEN` |
| API returns `500` | Lambda integration or function error | Check CloudWatch logs for the Lambda |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid JWTs before Lambda runs |

## Cleanup

Delete API Gateway:

```bash
aws apigatewayv2 delete-api \
  --api-id "$API_ID" \
  --region "$AWS_REGION"
```

Delete Lambda functions:

```bash
aws lambda delete-function \
  --function-name "$JEDI_FUNCTION" \
  --region "$AWS_REGION"

aws lambda delete-function \
  --function-name "$SITH_FUNCTION" \
  --region "$AWS_REGION"
```

Delete Cognito user pool:

```bash
aws cognito-idp delete-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"
```

Detach and delete the Lambda role:

```bash
aws iam detach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role \
  --role-name "$LAMBDA_ROLE_NAME"
```

## Final Check

You have completed the lab when you can explain this flow without looking:

```text
SECRET_HASH proves the app client secret
USER_AUTH starts negotiation
SELECT_CHALLENGE lets the client choose PASSWORD
PASSWORD validates the primary factor
SOFTWARE_TOKEN_MFA validates the second factor
Cognito issues JWT tokens
API Gateway validates the access token
Lambda only runs after authorization succeeds
CloudWatch proves what actually happened
```

## References

* [AWS CLI `initiate-auth`](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html)
* [AWS CLI `respond-to-auth-challenge`](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html)
* [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
* [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
* [API Gateway HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
* [Lambda proxy integrations for HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)

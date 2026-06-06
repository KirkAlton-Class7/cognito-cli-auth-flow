# Cognito Auth Flow - HTTPS Lab - CLI

This lab teaches the HTTPS/HTTP API implementation of the Cognito auth flow. You will build most resources with CLI commands when possible, and conceptual checkpoints will explain why each step matters.

This flow uses:

- Chewbacca test user
- Cognito User Pool
- default public app client for token helper scripts
- additional secret-bearing CLI app client for SECRET_HASH
- USER_AUTH / SELECT_CHALLENGE
- PASSWORD
- SOFTWARE_TOKEN_MFA
- Cognito access token
- API Gateway HTTP API JWT authorizer
- protected /prod/jedi and /prod/sith Lambda routes

> [!IMPORTANT]
> HTTP API routes are protected with a Cognito JWT authorizer. Use a newly generated Cognito **access token** for protected route tests. The HTTP API JWT authorizer validates the token issuer and audience before Lambda runs.

## Prerequisites

Install or confirm these tools:

```bash
aws --version
jq --version
python3 --version
zip --version
```

Confirm AWS identity:

```bash
aws sts get-caller-identity
```

Set the repo root:

```bash
export REPO_ROOT="<COGNITO_CLI_AUTH_FLOW_REPO_ROOT>"
cd "$REPO_ROOT"
```

Example:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
cd "$REPO_ROOT"
```

## 1. Create And Load The Environment File

An environment file helps simplify deployment and provides a record of planned values and resource outputs. You will copy the dotenv template, rename the copy to `.env`, update initial values, then reload it before running commands that depend on those values.

Copy the template:

```bash
cp "$REPO_ROOT/HTTPS/labs/cognito-auth-flow-HTTPS/env.example" \
  "$REPO_ROOT/HTTPS/labs/cognito-auth-flow-HTTPS/.env"
```

Set the environment file path:

```bash
export LAB_ENV="$REPO_ROOT/HTTPS/labs/cognito-auth-flow-HTTPS/.env"
```

Get the AWS account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

Open `.env` in VS Code or your editor of choice:

```bash
code "$LAB_ENV"
```

In `.env`, update the foundational inputs and review the planned values before building:

```bash
REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
AWS_ACCOUNT_ID="123456789012"
AWS_REGION="us-east-1"
PROJECT_NAME="chewbacca-auth-http"
TEST_USERNAME="chewbacca"
TEST_EMAIL="chewbacca@example.com"
TEST_PASSWORD="Wookiee#2026!"
TEMP_PASSWORD="Wookiee#TEMP1!"
```

Save `.env`, then load it for the build phase:

```bash
set -a
source "$LAB_ENV"
set +a
```

Validate the starting values before building:

```bash
echo "AWS_REGION=$AWS_REGION"
echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID"
echo "PROJECT_NAME=$PROJECT_NAME"
echo "JEDI_FUNCTION=$JEDI_FUNCTION"
echo "SITH_FUNCTION=$SITH_FUNCTION"
echo "API_NAME=$API_NAME"
echo "USER_POOL_NAME=$USER_POOL_NAME"
echo "AUTHORIZER_NAME=$AUTHORIZER_NAME"
```

> [!NOTE]
> Keep stable infrastructure values in `.env`. Keep short-lived values like `SESSION`, `TOTP_CODE`, `SECRET_HASH`, `ACCESS_TOKEN`, `ID_TOKEN`, `REFRESH_TOKEN`, and full auth responses in the terminal only.

## 2. Create Lambda Execution Roles


### Commands

Create the Python role:

```bash
aws iam create-role \
  --role-name "$PYTHON_LAMBDA_ROLE_NAME" \
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

aws iam attach-role-policy \
  --role-name "$PYTHON_LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Create the Node role:

```bash
aws iam create-role \
  --role-name "$NODE_LAMBDA_ROLE_NAME" \
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

aws iam attach-role-policy \
  --role-name "$NODE_LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Export role ARNs:

```bash
export PYTHON_LAMBDA_ROLE_ARN=$(aws iam get-role \
  --role-name "$PYTHON_LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text)

export NODE_LAMBDA_ROLE_ARN=$(aws iam get-role \
  --role-name "$NODE_LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text)

echo "$PYTHON_LAMBDA_ROLE_ARN"
echo "$NODE_LAMBDA_ROLE_ARN"
```

Give IAM a few seconds to propagate.


## 3. Package Lambda Code

Package the shared Lambda handlers with the default filenames expected by the Lambda console handlers.

```bash
cd "$REPO_ROOT/shared/lambda-code"

cp jedi_python.py lambda_function.py
zip jedi-python.zip lambda_function.py

cp sith_node.js index.js
zip sith-node.zip index.js
```

Validation:

```bash
ls -lh jedi-python.zip sith-node.zip
```

Packaging confirmation:

# TODO: Updated Screenshot
![Package Lambda ZIP files](/assets/images/095-package-lambda-zips.png)

## 4. Create The Lambda Functions

Create both Lambda functions from the packaged ZIP files, then export the function ARNs for API Gateway integration.

### Commands

Create the functions:

```bash
aws lambda create-function \
  --function-name "$JEDI_FUNCTION" \
  --runtime python3.12 \
  --role "$PYTHON_LAMBDA_ROLE_ARN" \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://jedi-python.zip \
  --region "$AWS_REGION"

aws lambda create-function \
  --function-name "$SITH_FUNCTION" \
  --runtime nodejs20.x \
  --role "$NODE_LAMBDA_ROLE_ARN" \
  --handler index.handler \
  --zip-file fileb://sith-node.zip \
  --region "$AWS_REGION"
```

Export the function ARNs:

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

echo "$JEDI_FUNCTION_ARN"
echo "$SITH_FUNCTION_ARN"
```

Function ARN export validation:

# TODO: Updated Screenshot
![Export function ARNs and validate](/assets/images/110-validate-function-arns.png)

## 5. Test Lambda Directly

Invoke the Python Lambda:

```bash
aws lambda invoke \
  --function-name "$JEDI_FUNCTION" \
  --payload '{"queryStringParameters":{"name":"Chewbacca"}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/chewbacca-rest-jedi-response.json \
  --region "$AWS_REGION"

jq . /tmp/chewbacca-rest-jedi-response.json
```

Expected:

```text
Jedi route returns 200 and a Python Jedi Council message.
```

Jedi Python invoke success:

# TODO: Updated Screenshot
![Jedi Python invoke success](/assets/images/027-jedi-python-invoke-success.png)

Invoke the Node Lambda:

```bash
aws lambda invoke \
  --function-name "$SITH_FUNCTION" \
  --payload '{"queryStringParameters":{"name":"Chewbacca"}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/chewbacca-rest-sith-response.json \
  --region "$AWS_REGION"

jq . /tmp/chewbacca-rest-sith-response.json
```

Expected:

```text
Sith route returns 200 and a Node Sith message.
```

Sith Node invoke success:

# TODO: Updated Screenshot
![Sith Node invoke success](/assets/images/023-sith-node-invoke-success.png)

## 6. Create The HTTP API

Console path: **API Gateway** -> **Create API** -> **HTTP API** -> API name from `API_NAME`.

> [!IMPORTANT]
> Keep these values handy for route tests and authorizer setup:

| Parameter | Console Location | Value |
| --- | --- | --- |
| API name | API Gateway HTTP API details | `chewbacca-auth-http-api` |
| API ID | API Gateway HTTP API details | `<API_ID>` |
| Invoke URL / endpoint | API Gateway stage details | `<API_ENDPOINT>` |
| Stage name | API Gateway stages | `prod` |

Equivalent CLI reference:

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

## 7. Add HTTP API Routes And Lambda Proxy Integrations

In the console, add Lambda integrations for `jedi` and `sith`, then create the `GET /jedi` and `GET /sith` routes. Keep the `prod` stage auto-deployed.

Equivalent CLI reference for the Jedi integration:

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

## 8. Test Unprotected HTTP API Paths Without A Token

Before adding the authorizer, prove routing works. These requests should return `200` and create Lambda logs.

This checkpoint proves the HTTP API route, Lambda integration, Lambda permission, and function code work before authorization is added.

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
curl -i "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected:

```text
{"message":"Welcome Chewbacca. The Python Jedi Council accepts your request.",...}
{"message":"WELCOME CHEWBACCA. THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.",...}
```

Both unprotected route tests:

# TODO: Updated Screenshot
![Unprotected API path tests](/assets/images/015-unprotected-api-tests.png)

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show API Gateway event payloads.
- The event shape is different from the direct Lambda test payload.

## 9. Create The Cognito User Pool

### Commands

```bash
export USER_POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "$USER_POOL_NAME" \
  --mfa-configuration OFF \
  --alias-attributes email \
  --auto-verified-attributes email \
  --schema \
    Name=name,AttributeDataType=String,Required=true,Mutable=true \
    Name=birthdate,AttributeDataType=String,Required=true,Mutable=true \
    Name=phone_number,AttributeDataType=String,Required=true,Mutable=true \
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

```bash
export COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"
export USER_POOL_ARN="arn:aws:cognito-idp:${AWS_REGION}:${AWS_ACCOUNT_ID}:userpool/${USER_POOL_ID}"

echo "$USER_POOL_ID"
echo "$COGNITO_ISSUER"
echo "$USER_POOL_ARN"
```

## 10. Enable Software Token MFA

### Commands

```bash
aws cognito-idp set-user-pool-mfa-config \
  --user-pool-id "$USER_POOL_ID" \
  --mfa-configuration ON \
  --software-token-mfa-configuration Enabled=true \
  --region "$AWS_REGION"
```

> [!NOTE]
> If you want an easier enrollment path while testing, use `OPTIONAL` instead of `ON`. The managed login flow in this lab intentionally walks the user through authenticator setup, which is best practice for production use.

## 11. Configure App Clients

This build uses two app clients:

| Client | Secret | Purpose |
| --- | --- | --- |
| Default `chewbacca-auth-http-users` client | No secret | Managed login and token helper scripts |
| Additional `chewbacca-auth-http-cli-client` client | Secret | Manual CLI flow with `SECRET_HASH` |

### 11.1 Edit The Default No-Secret App Client

#### Commands

Look up the default app client from the CLI:

```bash
export DEFAULT_CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id "$USER_POOL_ID" \
  --query "UserPoolClients[?ClientName=='${DEFAULT_APP_CLIENT_NAME}'].ClientId | [0]" \
  --output text \
  --region "$AWS_REGION")

export COGNITO_PUBLIC_CLIENT_ID="$DEFAULT_CLIENT_ID"
```

### 11.2 Create The Additional Secret-Bearing CLI App Client

> [!IMPORTANT]
> This step is optional: Only create a secret-bearing app client if you need to validate `SECRET_HASH` flows.

Create this app client only when you need to validate `SECRET_HASH` flows.

#### Commands

Create the secret-bearing app client:

```bash
export CLIENT_JSON=$(aws cognito-idp create-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-name "$USER_POOL_CLIENT_NAME" \
  --generate-secret \
  --explicit-auth-flows ALLOW_USER_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --access-token-validity 60 \
  --id-token-validity 60 \
  --refresh-token-validity 1 \
  --token-validity-units AccessToken=minutes,IdToken=minutes,RefreshToken=days \
  --query 'UserPoolClient' \
  --output json \
  --region "$AWS_REGION")

export CLIENT_ID=$(echo "$CLIENT_JSON" | jq -r '.ClientId')
export CLIENT_SECRET=$(echo "$CLIENT_JSON" | jq -r '.ClientSecret')
```

Describe and validate the app client:

```bash
export CLIENT_JSON=$(aws cognito-idp describe-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --query 'UserPoolClient' \
  --output json \
  --region "$AWS_REGION")

echo "$CLIENT_ID"
echo "${CLIENT_SECRET:0:8}..."
echo "$CLIENT_JSON" | jq '{ClientName,ExplicitAuthFlows,AccessTokenValidity,IdTokenValidity,RefreshTokenValidity,TokenValidityUnits}'
```

### 11.3 Create Managed Login Styling

#### Required Console Step

1. In the user pool, click **Branding**.
2. Click **Managed login**.
3. Click **Create style** in the styles tile.

> [!NOTE]
> Cognito managed login may show a browser error if a login page style has not been created and assigned. Create the style before using **View login page**.

If you try to view the login page before creating a style, you may see this browser error:

# TODO: Updated Screenshot
![Login page error before style setup](/assets/images/039-login-page-style-error.png)

# TODO: Updated Screenshot
![Select create style](/assets/images/106-select-create-login-style.png)

4. Select `chewbacca-auth-http-cli-client`.

# TODO: Updated Screenshot
![Select CLI app client for login style](/assets/images/062-select-login-style-app-client.png)

5. Click **Create**.

# TODO: Updated Screenshot
![Login style creation success](/assets/images/016-login-style-created.png)

6. Click the **Assigned app client** to return to the app client page.
7. Click **View login page**.

# TODO: Updated Screenshot
![Select view login page](/assets/images/086-select-view-login-page.png)

8. Confirm the CLI app client login page opens.

# TODO: Updated Screenshot
![CLI app client login page](/assets/images/087-app-client-login-page.png)

## 12. Create The Test User

This lab uses the admin-created user flow, then sets a permanent password from the CLI. You still create the managed login page so the hosted Cognito experience is present and can be compared with the CLI flow.

### 12.1 Admin Create The User

#### Commands

```bash
aws cognito-idp admin-create-user \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEST_USERNAME" \
  --temporary-password "$TEMP_PASSWORD" \
  --user-attributes \
    Name=email,Value="$TEST_EMAIL" \
    Name=email_verified,Value=true \
    Name=name,Value="Chewbacca Raaawr" \
    Name=phone_number,Value="+15555550100" \
  --message-action SUPPRESS \
  --region "$AWS_REGION"
```

Set a permanent password from the CLI if you are not using managed login to complete the temporary-password challenge:

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

## 13. Add The HTTP API JWT Authorizer

Create the HTTP API JWT authorizer:

Console path: open the HTTP API -> **Authorization** -> **Manage authorizers** -> **Create**. Use a JWT authorizer with issuer `COGNITO_ISSUER`, audience `CLIENT_ID`, and identity source `$request.header.Authorization`. Attach it to `GET /jedi` and `GET /sith`.

> [!IMPORTANT]
> Keep these values handy for validation and troubleshooting:

| Parameter | Console Location | Value |
| --- | --- | --- |
| Authorizer name | HTTP API authorizer details | `chewbacca-auth-http-cognito-jwt` |
| Authorizer ID | HTTP API authorizer details | `<COGNITO_AUTHORIZER_ID>` |
| Issuer | Cognito user pool issuer URL | `<COGNITO_ISSUER>` |
| Audience | Cognito app client ID | `<CLIENT_ID>` |
| Identity source | Authorizer identity source | `$request.header.Authorization` |

Equivalent CLI reference:

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

Validate the authorizer screenshot:

# TODO: Updated Screenshot
![Validate authorizer](/assets/images/006-validate-authorizer.png)

Validation:

```bash
aws apigatewayv2 get-authorizer \
  --api-id "$API_ID" \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

## 14. Test Authorizer Enforcement Without A Token

Test the protected routes before generating a valid token. These requests intentionally omit the `Authorization` header. API Gateway should reject them at the JWT authorizer layer before Lambda runs.

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

```bash
curl -i "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected:

```text
HTTP/2 401
content-type: application/json
...

{"message":"Unauthorized"}
```

Unauthorized response confirmation:

# TODO: Updated Screenshot
![Authorizer enforcement without token](/assets/images/109-authorizer-no-token-test.png)

Validation:

- Missing token returns `401` on both protected routes.
- Lambda logs do not appear for the denied request.
- If the request still returns `200`, the authorizer is not attached to the route or the latest API configuration is not active.

## 15. MFA Enrollment And Manual Authentication Flow

This section uses the secret-bearing CLI app client and teaches `SECRET_HASH`.

Export aliases used by the auth commands:

```bash
export USERNAME="$TEST_USERNAME"
export USER_PASSWORD="$TEST_PASSWORD"
```

Generate `SECRET_HASH`:

```bash
cd "$REPO_ROOT"

export SECRET_HASH=$(python3 shared/scripts/secret_hash.py \
  "$USERNAME" \
  "$CLIENT_ID" \
  "$CLIENT_SECRET")

echo "${SECRET_HASH:0:20}"
```

Secret hash generation:

# TODO: Updated Screenshot
![Generate secret hash manually](/assets/images/045-generate-secret-hash.png)

Secret hash export confirmation:

# TODO: Updated Screenshot
![Export secret hash](/assets/images/079-export-secret-hash.png)

### 15.1 Enroll TOTP With A Temporary Access Token

Use `USER_PASSWORD_AUTH` to obtain an access token for MFA setup. This access token is only used for enrollment.

```bash
aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$USERNAME",PASSWORD="$USER_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION" | jq
```

Initial TOTP setup attempt:

# TODO: Updated Screenshot
![Initial TOTP MFA setup attempt](/assets/images/055-initial-totp-mfa-attempt.png)

Export the temporary access token:

```bash
export TEMP_ACCESS_TOKEN=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$USERNAME",PASSWORD="$USER_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION" \
  --query 'AuthenticationResult.AccessToken' \
  --output text)
```

Associate a software token:

```bash
aws cognito-idp associate-software-token \
  --access-token "$TEMP_ACCESS_TOKEN" \
  --region "$AWS_REGION" | jq
```

Expected:

```json
{
  "SecretCode": "ABCDEFGHIJKLMNOP"
}
```

Associate software token:

# TODO: Updated Screenshot
![Associate software token](/assets/images/018-associate-software-token.png)

Copy `SecretCode` into your authenticator app to store the shared secret and generate TOTP codes for future authentication.

# TODO: Updated Screenshot
![Add Secret Code to Authenticator](/assets/images/105-authenticator-secret-setup.png)

# TODO: Updated Screenshot
![TOTP Codes in Authenticator](/assets/images/092-authenticator-code-generated.png)


Verify the software token with a valid TOTP code from your authenticator app:

```bash
export TOTP_CODE="<FRESH_6_DIGIT_CODE>"

aws cognito-idp verify-software-token \
  --access-token "$TEMP_ACCESS_TOKEN" \
  --user-code "$TOTP_CODE" \
  --friendly-device-name "Chewbacca CLI HTTPS" \
  --region "$AWS_REGION" | jq
```

Expected:

```json
{
  "Status": "SUCCESS"
}
```

Verify software token:

# TODO: Updated Screenshot
![Verify software token](/assets/images/104-verify-software-token.png)

Set software token MFA as preferred:

```bash
aws cognito-idp set-user-mfa-preference \
  --access-token "$TEMP_ACCESS_TOKEN" \
  --software-token-mfa-settings Enabled=true,PreferredMfa=true \
  --region "$AWS_REGION"
```

> [!NOTE]
> If the user already enrolled MFA through managed login, you can skip the enrollment commands and continue with `USER_AUTH`.

> [!NOTE]
> The two software-token screenshots above show the challenge-session enrollment variant. The primary command path in this lab uses `TEMP_ACCESS_TOKEN`; both approaches are valid Cognito enrollment patterns when the session or access token belongs to the same active authentication flow.

### 15.2 Alternate Option: Enroll TOTP Through Managed Login

This alternate path uses the hosted Cognito login page to enroll the same software-token MFA factor. It is useful for comparing the user-facing managed login experience with the CLI enrollment flow above. Both paths result in a user who can answer the later `SOFTWARE_TOKEN_MFA` challenge.

1. Open **View login page** from the CLI app client.

# TODO: Updated Screenshot
![View CLI app client login page](/assets/images/071-view-app-client-login-page.png)

2. Sign in with username `chewbacca` and the temporary password.

# TODO: Updated Screenshot
![CLI app sign-in](/assets/images/011-app-client-sign-in.png)

# TODO: Updated Screenshot
![CLI app sign-in screen](/assets/images/088-app-client-sign-in-screen.png)

3. Change the temporary password to the permanent password exported earlier.

# TODO: Updated Screenshot
![CLI app change password](/assets/images/047-app-client-change-password.png)

If the challenge session expires while you are learning the flow, restart the hosted login sequence and continue with a newly generated authenticator code.

# TODO: Updated Screenshot
![Session expired warning](/assets/images/100-session-expired-warning.png)

4. Continue to authenticator app setup.

# TODO: Updated Screenshot
![Set up authenticator app](/assets/images/024-set-up-authenticator-app.png)

5. Scan the QR code or click **Show secret key** and add the key manually to your authenticator app.

# TODO: Updated Screenshot
![Desktop authenticator setup](/assets/images/105-authenticator-secret-setup.png)

6. Use a valid TOTP code from your authenticator app.

# TODO: Updated Screenshot
![Desktop authenticator code generated](/assets/images/092-authenticator-code-generated.png)

7. Complete sign-in.

# TODO: Updated Screenshot
![Successful sign-in](/assets/images/032-successful-sign-in.png)

After this path, continue with `USER_AUTH`. You do not need to repeat the CLI software-token enrollment commands unless you want to practice both methods.

### 15.3 Start `USER_AUTH`

The client identifies the user. Cognito returns available challenges.

```bash
export AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="$USERNAME",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")

echo "$AUTH_RESPONSE" | jq
```

Expected:

```json
{
  "ChallengeName": "SELECT_CHALLENGE",
  "Session": "AYABe...<SELECT_CHALLENGE_SESSION>",
  "AvailableChallenges": ["PASSWORD", "PASSWORD_SRP"]
}
```

Export the session:

```bash
export SESSION=$(echo "$AUTH_RESPONSE" | jq -r '.Session')
echo "${SESSION:0:20}"
```

`USER_AUTH` returns `SELECT_CHALLENGE`:

# TODO: Updated Screenshot
![Start USER_AUTH and receive SELECT_CHALLENGE](/assets/images/096-user-auth-select-challenge.png)

### 15.4 Answer `SELECT_CHALLENGE` With `PASSWORD`

```bash
export PASSWORD_CHALLENGE_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="$USERNAME",ANSWER="PASSWORD",PASSWORD="$USER_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")

echo "$PASSWORD_CHALLENGE_RESPONSE" | jq
```

Expected:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>"
}
```

Update the session:

```bash
export SESSION=$(echo "$PASSWORD_CHALLENGE_RESPONSE" | jq -r '.Session')
```

> [!WARNING]
> Do not reuse the `SELECT_CHALLENGE` session for MFA. The password step returns a new session.

`SELECT_CHALLENGE` answered with `PASSWORD`:

# TODO: Updated Screenshot
![Answer SELECT_CHALLENGE with PASSWORD](/assets/images/075-select-challenge-password.png)

### 15.5 Respond To `SOFTWARE_TOKEN_MFA`

Use a valid TOTP code from your authenticator app:

```bash
export TOTP_CODE="<FRESH_6_DIGIT_CODE>"

export MFA_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="$USERNAME",SOFTWARE_TOKEN_MFA_CODE="$TOTP_CODE",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")

echo "$MFA_RESPONSE" | jq
```

MFA challenge response:

# TODO: Updated Screenshot
![Respond to SOFTWARE_TOKEN_MFA](/assets/images/080-software-token-mfa-response.png)

Export tokens:

```bash
export ACCESS_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.AccessToken')
export ID_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.IdToken')
export REFRESH_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.RefreshToken')

echo "${ACCESS_TOKEN:0:24}"
echo "${ID_TOKEN:0:24}"
echo "${REFRESH_TOKEN:0:24}"
```

Returned token export:

# TODO: Updated Screenshot
![Export returned tokens](/assets/images/098-export-returned-tokens.png)

Authentication result:

# TODO: Updated Screenshot
![MFA response with AuthenticationResult](/assets/images/021-mfa-authentication-result.png)

> [!IMPORTANT]
> Use `$ACCESS_TOKEN` for the protected HTTP API route tests. The ID token is still useful for inspecting identity claims, but the access token is the clearest token choice for these route checks.

## 16. Token Helper Script Authentication With The No-Secret Client

This section uses the default no-secret app client named `chewbacca-auth-http-users`.

Export token helper script values:

```bash
export COGNITO_USERNAME="$TEST_USERNAME"
export COGNITO_PASSWORD="$TEST_PASSWORD"
export API_BASE="${API_ENDPOINT}/prod"

echo "$COGNITO_PUBLIC_CLIENT_ID"
echo "$COGNITO_USERNAME"
echo "$API_BASE"
```

If you did not already export the no-secret client ID:

```bash
export COGNITO_PUBLIC_CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id "$USER_POOL_ID" \
  --query "UserPoolClients[?ClientName=='${DEFAULT_APP_CLIENT_NAME}'].ClientId | [0]" \
  --output text \
  --region "$AWS_REGION")
```

Public app client lookup for token helper scripts:

# TODO: Updated Screenshot
![Create public helper client](/assets/images/042-create-public-helper-client.png)

Install dependencies for token helper scripts:

```bash
cd "$REPO_ROOT"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Token helper script dependency install:

# TODO: Updated Screenshot
![Install helper script dependencies](/assets/images/064-install-helper-dependencies.png)

Run the `easier_get_token.py` script:

```bash
python shared/scripts/easier_get_token.py
```

`easier_get_token.py` run output:

# TODO: Updated Screenshot
![Export helper script values and run easier_get_token](/assets/images/093-run-easier-get-token.png)

`easier_get_token.py` token response:

# TODO: Updated Screenshot
![Easier token helper output](/assets/images/103-easier-token-helper-output.png)

`easier_get_token.py` token output:

# TODO: Updated Screenshot
![Easier token helper token output](/assets/images/008-easier-token-output.png)

Run the `flavor_get_token.py` script:

```bash
python shared/scripts/flavor_get_token.py
```

`flavor_get_token.py` script output:

# TODO: Updated Screenshot
![Run flavor_get_token](/assets/images/033-run-flavor-get-token.png)

The `flavor_get_token.py` script should decode token claims and print curl examples for:

```text
${API_BASE}/jedi
${API_BASE}/sith
```

Curl examples from `flavor_get_token.py`:

# TODO: Updated Screenshot
![Helper-generated curl examples](/assets/images/003-helper-curl-examples.png)

Access token claims:

# TODO: Updated Screenshot
![Access token claims](/assets/images/050-access-token-claims.png)

Token helper script API test with access token:

# TODO: Updated Screenshot
![Helper API test with access token](/assets/images/012-helper-access-token-api-test.png)

> [!NOTE]
> These token helper scripts are convenience tools after the learning pass. If the selected app client has a secret, the script flow will fail because these scripts do not send `SECRET_HASH`.

## 17. Test Protected HTTP API Routes With Access Tokens

| Token | What it represents | Use in this lab |
| --- | --- | --- |
| Access token | Permission to call APIs | Use with API Gateway JWT authorizer |
| ID token | User identity/profile claims | Useful for inspecting user identity |
| Refresh token | Used to request new tokens | Keep private. Do not send to API Gateway |

For API testing, use:

```bash
Authorization: Bearer $ACCESS_TOKEN
```

## 18. Direct Flow Shortcut

After MFA is enabled, `USER_PASSWORD_AUTH` skips `SELECT_CHALLENGE` and goes directly to password validation, then MFA.

```bash
export DIRECT_AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$USERNAME",PASSWORD="$USER_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")

echo "$DIRECT_AUTH_RESPONSE" | jq
```

Expected:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>"
}
```

Direct flow shortcut response:

# TODO: Updated Screenshot
![Direct flow shortcut to SOFTWARE_TOKEN_MFA](/assets/images/061-direct-flow-mfa-shortcut.png)

This shortcut is useful after the manual learning pass, but it does not teach the `SELECT_CHALLENGE` negotiation step.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unable to verify secret hash` | Wrong username, client ID, client secret, or copied hash | Regenerate `SECRET_HASH` using the exact username, client ID, and client secret |
| `InvalidParameterException` for `USER_AUTH` | App client does not allow `ALLOW_USER_AUTH` | Edit the app client and enable choice-based sign-in |
| `Invalid session` | Session reused from the wrong flow, user, app client, or expired challenge chain | Restart from `USER_AUTH` and use each new session in order |
| `CodeMismatchException` | Expired or incorrect TOTP code | Wait for a newly generated code and retry |
| MFA not challenged after password | User has not enrolled TOTP or MFA preference is not set | Complete MFA enrollment again |
| `{"message":"Unauthorized"}` with token | Wrong token type, expired token, bad header, issuer/audience mismatch, or stale route configuration | Use a newly generated `$ACCESS_TOKEN`, confirm the JWT authorizer issuer and audience, and recheck the route authorizer attachment |
| Route still public | JWT authorizer is not attached to the route, or the route update is not active yet | Recheck the route authorizer attachment and wait for the auto-deployed `prod` stage to apply the route update |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid requests before Lambda runs |

## Validation Checklist

Use this checklist before you consider the HTTPS lab complete:

- [ ] Copy `env.example` to `.env`, update planned values, and reload it before dependent commands.
- [ ] Package both shared Lambda handlers from `shared/lambda-code/`.
- [ ] Create or configure separate Lambda roles for the Python and Node functions.
- [ ] Create the Jedi Python Lambda and Sith Node Lambda.
- [ ] Invoke both Lambda functions directly and confirm HTTP `200` responses.
- [ ] Create the HTTP API, Lambda integrations, `/jedi` route, `/sith` route, and `prod` stage.
- [ ] Test both public routes before adding Cognito and confirm they return HTTP `200`.
- [ ] Create the Cognito user pool, app clients, Chewbacca user, and MFA configuration.
- [ ] Create the managed login page app client without a client secret for browser login and token helper scripts.
- [ ] Optionally create the secret-bearing app client when you want to validate `SECRET_HASH` flows.
- [ ] Generate a valid `SECRET_HASH` when using the secret-bearing app client.
- [ ] Run the manual `USER_AUTH` flow and observe the `SELECT_CHALLENGE` response.
- [ ] Copy each Cognito `Session` value into the next matching challenge response.
- [ ] Complete the `PASSWORD` challenge and the `SOFTWARE_TOKEN_MFA` challenge with a valid TOTP code.
- [ ] Export the access token, ID token, and refresh token after MFA succeeds.
- [ ] Create the HTTP API JWT authorizer with the Cognito issuer and public app client audience.
- [ ] Attach the JWT authorizer to both protected routes.
- [ ] Confirm both protected routes return HTTP `401` without an `Authorization` header.
- [ ] Confirm both protected routes return HTTP `200` with a valid access token.
- [ ] Run `easier_get_token.py` and `flavor_get_token.py` after the manual pass.
- [ ] Confirm CloudWatch logs appear only after API Gateway authorization succeeds.
- [ ] Run the lab teardown from `lab-docs/TEARDOWN_HTTPS.md` when you are ready to remove the lab resources.

## Concept Takeaways

- Cognito owns user authentication, challenge negotiation, MFA validation, and JWT issuance.
- `SECRET_HASH` proves knowledge of an app client secret; it does not replace the user password or MFA factor.
- `USER_AUTH` makes the challenge sequence visible: `SELECT_CHALLENGE`, `PASSWORD`, then `SOFTWARE_TOKEN_MFA`.
- Cognito `Session` values are chain-specific. Reusing a session from another flow, user, or challenge can break authentication.
- HTTP API routes are protected by a JWT authorizer that checks issuer, audience, token validity, and route authorization settings.
- HTTP API uses the access token for protected API route calls in this lab.
- HTTP API stages can auto-deploy route and authorizer changes, unlike REST API stage redeployments.
- API Gateway rejects unauthorized requests before Lambda runs, so missing Lambda logs can be proof that authorization blocked the request.
- CloudWatch is the final evidence source for whether API Gateway reached Lambda.

## Final Check

You are ready to leave this HTTPS lab when you can explain the full path without looking:

```text
Chewbacca authenticates with Cognito
Cognito negotiates PASSWORD and SOFTWARE_TOKEN_MFA challenges
Cognito issues JWT tokens
API Gateway HTTP API validates the access token with a JWT authorizer
Authorized requests reach the Jedi and Sith Lambda routes
Unauthorized requests stop at API Gateway
CloudWatch proves which requests reached Lambda
```

## References

* [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
* [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
* [API Gateway HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
* [Lambda proxy integrations for HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)

* [Amazon Cognito InitiateAuth API](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html)
* [Amazon Cognito RespondToAuthChallenge API](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_RespondToAuthChallenge.html)
* [Computing Cognito secret hash values](https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html#cognito-user-pools-computing-secret-hash)
* [JWT introduction](https://jwt.io/introduction)

### AWS CLI Command References

Every AWS CLI command used in this lab is linked below to the direct AWS command reference page.

| Command | AWS CLI reference |
| --- | --- |
| `aws sts get-caller-identity` | [sts get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html) |
| `aws iam create-role` | [iam create-role](https://docs.aws.amazon.com/cli/latest/reference/iam/create-role.html) |
| `aws iam attach-role-policy` | [iam attach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/attach-role-policy.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |
| `aws lambda create-function` | [lambda create-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/create-function.html) |
| `aws lambda get-function` | [lambda get-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function.html) |
| `aws lambda invoke` | [lambda invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html) |
| `aws lambda add-permission` | [lambda add-permission](https://docs.aws.amazon.com/cli/latest/reference/lambda/add-permission.html) |
| `aws apigatewayv2 create-api` | [apigatewayv2 create-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-api.html) |
| `aws apigatewayv2 get-api` | [apigatewayv2 get-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-api.html) |
| `aws apigatewayv2 create-integration` | [apigatewayv2 create-integration](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-integration.html) |
| `aws apigatewayv2 create-route` | [apigatewayv2 create-route](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-route.html) |
| `aws apigatewayv2 create-stage` | [apigatewayv2 create-stage](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-stage.html) |
| `aws apigatewayv2 create-authorizer` | [apigatewayv2 create-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-authorizer.html) |
| `aws apigatewayv2 get-routes` | [apigatewayv2 get-routes](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-routes.html) |
| `aws apigatewayv2 update-route` | [apigatewayv2 update-route](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/update-route.html) |
| `aws apigatewayv2 get-authorizer` | [apigatewayv2 get-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-authorizer.html) |
| `aws cognito-idp create-user-pool` | [cognito-idp create-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/create-user-pool.html) |
| `aws cognito-idp set-user-pool-mfa-config` | [cognito-idp set-user-pool-mfa-config](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-pool-mfa-config.html) |
| `aws cognito-idp create-user-pool-client` | [cognito-idp create-user-pool-client](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/create-user-pool-client.html) |
| `aws cognito-idp admin-create-user` | [cognito-idp admin-create-user](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-create-user.html) |
| `aws cognito-idp admin-set-user-password` | [cognito-idp admin-set-user-password](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-set-user-password.html) |
| `aws cognito-idp admin-get-user` | [cognito-idp admin-get-user](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-get-user.html) |
| `aws cognito-idp initiate-auth` | [cognito-idp initiate-auth](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html) |
| `aws cognito-idp associate-software-token` | [cognito-idp associate-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/associate-software-token.html) |
| `aws cognito-idp verify-software-token` | [cognito-idp verify-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/verify-software-token.html) |
| `aws cognito-idp set-user-mfa-preference` | [cognito-idp set-user-mfa-preference](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-mfa-preference.html) |
| `aws cognito-idp respond-to-auth-challenge` | [cognito-idp respond-to-auth-challenge](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html) |

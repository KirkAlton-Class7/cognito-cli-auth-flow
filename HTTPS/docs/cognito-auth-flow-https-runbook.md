# Chewbacca Cognito CLI Auth Flow Lab - HTTPS Version

HTTP API implementation of the Chewbacca Cognito CLI auth-flow lab.<br>
View the REST version [here](../../REST/README.md) if you prefer that implementation.<br><br>

This lab rebuilds the class workflow that shows how Cognito authentication works from the command line after the infrastructure is created in the AWS Console. It keeps the architecture intentionally small: one user pool, one app client, two Lambda functions, one HTTP API, and a Cognito JWT authorizer.

> [!IMPORTANT]
> This folder documents the HTTP API implementation. The REST implementation uses the same Cognito flow but a different API Gateway command set and authorizer type.

## Build Mode

Use the **AWS Console** to create infrastructure:

```text
IAM role
Lambda functions
HTTP API
Lambda integrations
Cognito user pool
Cognito app client
Chewbacca test user
HTTP API JWT authorizer
```

Use the **CLI** after the console build to test authentication. Run it in two passes:

```text
Manual pass:
  generate SECRET_HASH
  run USER_AUTH
  inspect the raw SELECT_CHALLENGE response
  copy the Session value by hand
  choose PASSWORD
  copy the new Session value by hand
  complete SOFTWARE_TOKEN_MFA
  inspect the returned tokens

Export pass:
  export generated IDs and names
  export Session values
  export JWT tokens
  call protected routes with curl
```

> [!NOTE]
> CLI blocks in the infrastructure sections are equivalent reference commands. The intended lab flow is console setup first, then CLI authentication and validation.

> [!IMPORTANT]
> Do the manual CLI pass first. Copying challenge `Session` values by hand is not busywork here; it is the fastest way to understand how Cognito moves from `SELECT_CHALLENGE` to `PASSWORD` to `SOFTWARE_TOKEN_MFA`. After that, use the export path to repeat the flow quickly.

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
| Original class notes | Recovered `USER_AUTH`, challenge selection, MFA, and token-handling workflow |
| Original Lesson B Lambda lab | Simple API Gateway + Lambda pattern that shaped the Jedi/Sith route handlers |
| [`../../shared/lambda-code`](../../shared/lambda-code/) | Simplified Chewbacca/Jedi/Sith Lambda functions for this runbook |
| [`../../shared/scripts/secret_hash.py`](../../shared/scripts/secret_hash.py) | Helper script for Cognito app clients with a client secret |

## Prerequisites For CLI Testing

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
export LAB_REPO="<COGNITO_CLI_AUTH_FLOW_REPO_ROOT>"
cd "$LAB_REPO"
```

Example:

```bash
export LAB_REPO="/Users/kirk/cognito-cli-auth-flow"
cd "$LAB_REPO"
```

## 1. Record And Export Lab Values For CLI Testing

Create the infrastructure in the AWS Console using these names, then export the same values in your terminal before running the authentication flow.

```bash
export AWS_REGION="us-west-2"
export PROJECT_NAME="chewbacca-auth-http"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"

export API_NAME="${PROJECT_NAME}-api"
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

Console path: **IAM** -> **Roles** -> **Create role** -> trusted entity **Lambda** -> attach `AWSLambdaBasicExecutionRole` -> role name from `LAMBDA_ROLE_NAME`.

Equivalent CLI reference:

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
cd "$LAB_REPO/shared/lambda-code"

zip jedi-python.zip jedi_python.py
zip sith-node.zip sith_node.js
```

Validation:

```bash
ls -lh *.zip
```

## 4. Create the Lambda Functions

Create the Jedi Python Lambda:

Console path: **Lambda** -> **Create function** -> **Author from scratch**. Use the function names, runtimes, handlers, and ZIP files shown below.

> [!IMPORTANT]
> Keep these values handy for API Gateway integration:

| Parameter | Console Location | Value |
| --- | --- | --- |
| Jedi function name | Lambda function overview | `chewbacca-auth-http-jedi-python` |
| Jedi function ARN | Lambda function overview -> **Function ARN** | `<JEDI_FUNCTION_ARN>` |
| Sith function name | Lambda function overview | `chewbacca-auth-http-sith-node` |
| Sith function ARN | Lambda function overview -> **Function ARN** | `<SITH_FUNCTION_ARN>` |
| Lambda execution role | Lambda function configuration -> **Permissions** | `chewbacca-auth-http-lambda-basic-role` |

Equivalent CLI reference:

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

Expected output:

```text
statusCode: 200
body contains: The Python Jedi Council accepts your request.
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

Expected output:

```text
statusCode: 200
body contains: THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.
```

Validation:

- Jedi Python returns a JSON body with `The Python Jedi Council accepts your request.`
- Sith Node returns a JSON body with `THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.`
- CloudWatch has log groups for both functions.

## 6. Create the HTTP API

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

## 7. Add Lambda Integrations

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

## 8. Test the Public API Before Auth

Before adding Cognito, prove routing works.

```bash
curl "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
curl "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected output:

```text
{"message":"Welcome Chewbacca. The Python Jedi Council accepts your request.",...}
{"message":"WELCOME CHEWBACCA. THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.",...}
```

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show API Gateway event payloads.
- The event shape is different from the direct Lambda test payload.

## 9. Create the Cognito User Pool

Create the user pool first with MFA off. Cognito requires SMS configuration when MFA is set to optional during `create-user-pool`, so software-token MFA is enabled after the pool exists.

Console path: **Amazon Cognito** -> **User pools** -> **Create user pool**. Use email sign-in and the password policy shown below. Leave MFA off during initial pool creation, then enable software-token MFA after the pool exists.

> [!IMPORTANT]
> Keep these values handy for app client setup, authorizer setup, and CLI authentication:

| Parameter | Console Location | Value |
| --- | --- | --- |
| User pool name | Cognito user pool details | `chewbacca-auth-http-users` |
| User pool ID | Cognito user pool details | `<USER_POOL_ID>` |
| Issuer URL | `https://cognito-idp.<REGION>.amazonaws.com/<USER_POOL_ID>` | `<COGNITO_ISSUER>` |
| Region | AWS console region selector | `us-west-2` |

### 9.1 Create The User Pool

Equivalent CLI reference:

```bash
export USER_POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "$USER_POOL_NAME" \
  --mfa-configuration OFF \
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

### 9.2 Enable Software Token MFA

```bash
aws cognito-idp set-user-pool-mfa-config \
  --user-pool-id "$USER_POOL_ID" \
  --mfa-configuration OPTIONAL \
  --software-token-mfa-configuration Enabled=true \
  --region "$AWS_REGION"
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

Console path: open the user pool -> **App clients** -> **Create app client**. Enable the auth flows shown below, generate a client secret, and set token expiration for the lab:

| Token | Expiration |
| --- | --- |
| Access token | `15 minutes` |
| ID token | `15 minutes` |
| Refresh token | `1 day` |

> [!NOTE]
> The protected HTTP API route uses the access token. A 15-minute access token makes expiration behavior easy to observe without waiting through a long default session.

> [!IMPORTANT]
> Keep these values handy for `SECRET_HASH`, manual authentication, and the export-driven run:

| Parameter | Console Location | Value |
| --- | --- | --- |
| App client name | Cognito app client details | `chewbacca-auth-http-cli-client` |
| Client ID | Cognito app client details | `<CLIENT_ID>` |
| Client secret | Cognito app client details -> **Show client secret** | `<CLIENT_SECRET>` |
| Enabled auth flows | App client authentication flows | `ALLOW_USER_AUTH`, `ALLOW_USER_PASSWORD_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH` |

Token settings to verify:

| Token setting | Lab value |
| --- | --- |
| Access token validity | `15 minutes` |
| ID token validity | `15 minutes` |
| Refresh token validity | `1 day` |

Equivalent CLI reference:

```bash
export CLIENT_JSON=$(aws cognito-idp create-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-name "$USER_POOL_CLIENT_NAME" \
  --generate-secret \
  --explicit-auth-flows ALLOW_USER_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --access-token-validity 15 \
  --id-token-validity 15 \
  --refresh-token-validity 1 \
  --token-validity-units AccessToken=minutes,IdToken=minutes,RefreshToken=days \
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
echo "$CLIENT_JSON" | jq '{AccessTokenValidity,IdTokenValidity,RefreshTokenValidity,TokenValidityUnits}'
```

> [!IMPORTANT]
> Do not commit real Cognito client secrets. This lab prints only a short prefix for validation.

## 11. Create the Test User

Create `chewbacca` and suppress the welcome email:

Console path: open the user pool -> **Users** -> **Create user**. Use the username, email, and password values from the export block.

> [!IMPORTANT]
> Keep these values handy for the manual authentication run:

| Parameter | Console Location | Value |
| --- | --- | --- |
| Username | Cognito user details | `chewbacca` |
| Email | Cognito user attributes | `chewbacca@example.com` |
| Permanent password | Password set during user creation/reset | `Wookiee#2026!` |
| Email verified | Cognito user attributes | `true` |

Equivalent CLI reference:

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

## 12. Manual Authentication Run

Run the full authentication flow manually first. Do not use shell variables in this pass. The point is to see the values Cognito returns and move them into the next request yourself.

Use these placeholders in the manual commands:

| Placeholder | Where to get it |
| --- | --- |
| `<REGION>` | The lab region, such as `us-west-2` |
| `<CLIENT_ID>` | Cognito app client ID from Step 10 |
| `<CLIENT_SECRET>` | Cognito app client secret from Step 10 |
| `<USER_NAME>` | Test username from Step 11, such as `chewbacca` |
| `<USER_PASSWORD>` | Permanent password from Step 11 |
| `<SECRET_HASH>` | Output from the manual `secret_hash.py` command |
| `<TEMP_ACCESS_TOKEN>` | `AuthenticationResult.AccessToken` from the direct password auth response |
| `<TOTP_SECRET>` | `SecretCode` from `associate-software-token` |
| `<MFA_CODE>` | Current six-digit code from your authenticator app |
| `<SELECT_CHALLENGE_SESSION>` | `Session` from the `SELECT_CHALLENGE` response |
| `<SOFTWARE_TOKEN_MFA_SESSION>` | `Session` from the `SOFTWARE_TOKEN_MFA` challenge response |
| `<ACCESS_TOKEN>` | `AuthenticationResult.AccessToken` from the final MFA response |

> [!IMPORTANT]
> Complete this manual run before using the export-driven run. Copying the two different `Session` values by hand is what makes the Cognito challenge sequence visible.

### 12.1 Manual Check: Generate `SECRET_HASH`

`SECRET_HASH` is the client-secret proof that Cognito expects when an app client has a secret. The helper calculates the HMAC value from the username, app client ID, and client secret so the manual CLI requests match Cognito's documented `SECRET_HASH` requirement.

```bash
cd "$LAB_REPO"
python3 shared/scripts/secret_hash.py \
  "<USER_NAME>" \
  "<CLIENT_ID>" \
  "<CLIENT_SECRET>"
```

Expected output:

```text
<SECRET_HASH>
```

> [!IMPORTANT]
> Copy that output and use it as `<SECRET_HASH>` in the next manual commands.

### 12.2 Initial TOTP MFA Setup

Authenticate once with direct username-password auth to begin initial TOTP MFA setup. MFA is optional at this point, so Cognito should return temporary tokens.

> [!NOTE]
> Run this initial setup step only for a fresh test user that has not enrolled an authenticator app yet. If MFA is already enrolled, skip to **12.3 Manual Check: Start `USER_AUTH`**.

This `initiate-auth` call starts a username-password sign-in with the password sent in the request. In this initial setup pass, the goal is not to study challenge negotiation yet; it is to get a short-lived access token that can authorize the user's software-token MFA enrollment.

```bash
aws cognito-idp initiate-auth \
  --client-id "<CLIENT_ID>" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="<USER_NAME>",PASSWORD="<USER_PASSWORD>",SECRET_HASH="<SECRET_HASH>" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "ChallengeParameters": {},
  "AuthenticationResult": {
    "AccessToken": "eyJraWQiOiJNek1LXC8yZzgz...<ACCESS_TOKEN_PAYLOAD>...<ACCESS_TOKEN_SIGNATURE>",
    "ExpiresIn": 900,
    "TokenType": "Bearer",
    "RefreshToken": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...<REFRESH_TOKEN>",
    "IdToken": "eyJraWQiOiJnVkkrSDRcL0Ja...eyJ0b2tlbl91c2UiOiJpZCIsImVtYWlsIjoiY2hld2JhY2NhQGV4YW1wbGUuY29tIn0...<ID_TOKEN_SIGNATURE>"
  }
}
```

> [!NOTE]
> `ExpiresIn` follows the app client token validity. If the app client is still at the default one-hour validity, this value can appear as `3600` instead of `900`.

Use the temporary access token to request a software-token secret. `associate-software-token` begins TOTP setup and asks Cognito to generate the private key that your authenticator app will use. Cognito allows this call with either a signed-in user's access token or a valid challenge session; this lab uses the access token because it makes the bootstrap path easier to see.

```bash
aws cognito-idp associate-software-token \
  --access-token "<TEMP_ACCESS_TOKEN>" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "SecretCode": "<TOTP_SECRET>"
}
```

Add `<TOTP_SECRET>` to your authenticator app as a manual setup key. Then verify the current six-digit code. `verify-software-token` proves that the authenticator app and Cognito agree on the TOTP secret by checking the six-digit code generated from that shared key.

```bash
aws cognito-idp verify-software-token \
  --access-token "<TEMP_ACCESS_TOKEN>" \
  --user-code "<MFA_CODE>" \
  --friendly-device-name "Chewbacca CLI" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "Status": "SUCCESS"
}
```

Set software token MFA as preferred. `set-user-mfa-preference` activates software-token MFA for this user and marks it as the factor Cognito should challenge during future sign-in attempts.

```bash
aws cognito-idp set-user-mfa-preference \
  --access-token "<TEMP_ACCESS_TOKEN>" \
  --software-token-mfa-settings Enabled=true,PreferredMfa=true \
  --region "<REGION>"
```

Expected output:

```text
No output means the preference update succeeded.
```

> [!IMPORTANT]
> `<TEMP_ACCESS_TOKEN>` is only for MFA enrollment. If this token expires during setup, run the direct password auth command again and use the new access token.

### 12.3 Manual Check: Start `USER_AUTH`

`USER_AUTH` starts Cognito's choice-based authentication flow. Instead of sending the password immediately, the client identifies the user and asks Cognito which sign-in challenges are available. Cognito should answer with `SELECT_CHALLENGE` and a `Session` value that must be carried into the next command.

```bash
aws cognito-idp initiate-auth \
  --client-id "<CLIENT_ID>" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="<USER_NAME>",SECRET_HASH="<SECRET_HASH>" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "ChallengeName": "SELECT_CHALLENGE",
  "Session": "AYABe...<SELECT_CHALLENGE_SESSION>",
  "ChallengeParameters": {},
  "AvailableChallenges": [
    "PASSWORD",
    "PASSWORD_SRP"
  ]
}
```

Copy `<SELECT_CHALLENGE_SESSION>` into the next command.

> [!WARNING]
> A Cognito `Session` belongs to one specific challenge chain. If you answer `SELECT_CHALLENGE` with a session from `USER_PASSWORD_AUTH`, an older run, another app client, or another user, Cognito can return `Invalid session due to a mismatched auth flow`. Restart from **12.3 Manual Check: Start `USER_AUTH`** and copy the fresh `Session` from that response.

### 12.4 Manual Check: Choose `PASSWORD`

`respond-to-auth-challenge` answers the `SELECT_CHALLENGE` prompt. In this step, `ANSWER="PASSWORD"` tells Cognito which available sign-in method to use, and the same request supplies the password. If the primary factor succeeds and MFA is enabled, Cognito returns the next challenge plus a new `Session`.

```bash
aws cognito-idp respond-to-auth-challenge \
  --client-id "<CLIENT_ID>" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="<USER_NAME>",ANSWER="PASSWORD",PASSWORD="<USER_PASSWORD>",SECRET_HASH="<SECRET_HASH>" \
  --session "<SELECT_CHALLENGE_SESSION>" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>",
  "ChallengeParameters": {
    "FRIENDLY_DEVICE_NAME": "Chewbacca CLI",
    "USER_ID_FOR_SRP": "chewbacca"
  }
}
```

Copy `<SOFTWARE_TOKEN_MFA_SESSION>` into the next command.

> [!WARNING]
> Do not reuse the earlier `SELECT_CHALLENGE` session for MFA. The password challenge returns a new `Session`, and that new value is the only valid handoff into `SOFTWARE_TOKEN_MFA`.

### 12.5 Manual Check: Respond To `SOFTWARE_TOKEN_MFA`

This second `respond-to-auth-challenge` call answers the MFA prompt. The `Session` must be the one returned by the password step, and the MFA code must be current. A successful response ends the challenge chain and returns the Cognito token set.

```bash
aws cognito-idp respond-to-auth-challenge \
  --client-id "<CLIENT_ID>" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="<USER_NAME>",SOFTWARE_TOKEN_MFA_CODE="<MFA_CODE>",SECRET_HASH="<SECRET_HASH>" \
  --session "<SOFTWARE_TOKEN_MFA_SESSION>" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "ChallengeParameters": {},
  "AuthenticationResult": {
    "AccessToken": "eyJraWQiOiJNek1LXC8yZzgz...eyJ1c2VybmFtZSI6ImNoZXdiYWNjYSJ9...<ACCESS_TOKEN_SIGNATURE>",
    "ExpiresIn": 900,
    "TokenType": "Bearer",
    "RefreshToken": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...<REFRESH_TOKEN>",
    "IdToken": "eyJraWQiOiJnVkkrSDRcL0Ja...eyJlbWFpbCI6ImNoZXdiYWNjYUBleGFtcGxlLmNvbSJ9...<ID_TOKEN_SIGNATURE>"
  }
}
```

> [!NOTE]
> The real response contains full JWT/JWE strings. The examples shorten tokens for readability, while preserving their overall structure.

For the HTTP API route test, copy `<ACCESS_TOKEN>`.

> [!WARNING]
> Cognito challenge sessions are short-lived. If too much time passes between manual commands, restart from **12.3 Manual Check: Start `USER_AUTH`**.

## 13. Export-Driven Authentication Run

After completing the manual run, repeat the same authentication flow with shell exports. This pass is for repeatability and easier test reuse.

> [!IMPORTANT]
> If you are continuing in the same terminal session from the manual run and your variables are still set, continue directly to **13.1 Export `SECRET_HASH`**. If you opened a new terminal, skipped the manual run, or are returning later, collect the values below from the AWS Console and export them before continuing.

| Parameter | Console Location | Value |
| --- | --- | --- |
| Lab repo path | Local terminal | `<COGNITO_CLI_AUTH_FLOW_REPO_ROOT>` |
| AWS region | AWS Console region selector | `us-west-2` |
| App client ID | Cognito user pool -> App clients -> `<APP_CLIENT_NAME>` | `<CLIENT_ID>` |
| App client secret | Cognito user pool -> App clients -> `<APP_CLIENT_NAME>` -> show client secret | `<CLIENT_SECRET>` |
| Test username | Cognito user pool -> Users -> user details | `chewbacca` |
| Test password | Password set during user creation/reset | `<USER_PASSWORD>` |

Set the working directory:

```bash
export LAB_REPO="<COGNITO_CLI_AUTH_FLOW_REPO_ROOT>"
cd "$LAB_REPO"
```

Example:

```bash
export LAB_REPO="/Users/kirk/cognito-cli-auth-flow"
cd "$LAB_REPO"
```

Export the remaining values:

```bash
export AWS_REGION="us-west-2"
export CLIENT_ID="<CLIENT_ID>"
export CLIENT_SECRET="<CLIENT_SECRET>"
export TEST_USERNAME="chewbacca"
export TEST_PASSWORD="<USER_PASSWORD>"
```

Validation:

```bash
echo "$LAB_REPO"
echo "$AWS_REGION"
echo "$CLIENT_ID"
echo "${CLIENT_SECRET:0:8}..."
echo "$TEST_USERNAME"
```

> [!CAUTION]
> Do not print the full `CLIENT_SECRET` in shared terminals, screenshots, commits, or notes. Show only a short prefix when validating that the variable is loaded.

### 13.1 Export `SECRET_HASH`

This is the same client-secret proof from the manual pass, stored in a shell variable so the remaining commands can be repeated quickly without recopying the hash.

```bash
cd "$LAB_REPO"

export SECRET_HASH=$(python3 shared/scripts/secret_hash.py \
  "$TEST_USERNAME" \
  "$CLIENT_ID" \
  "$CLIENT_SECRET")

echo "${SECRET_HASH:0:20}"
```

Expected output:

```text
<first-20-characters-of-secret-hash>
```

### 13.2 Export Run: Start `USER_AUTH`

This repeats the choice-based `USER_AUTH` start step and stores Cognito's raw response. The important output is still the challenge `Session`; the export path simply lets `jq` carry it forward instead of copying it by hand.

```bash
export AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")

echo "$AUTH_RESPONSE" | jq
```

Expected output:

```json
{
  "ChallengeName": "SELECT_CHALLENGE",
  "Session": "AYABe...<SELECT_CHALLENGE_SESSION>",
  "ChallengeParameters": {},
  "AvailableChallenges": [
    "PASSWORD",
    "PASSWORD_SRP"
  ]
}
```

Export the session:

```bash
export SESSION=$(echo "$AUTH_RESPONSE" | jq -r '.Session')
echo "${SESSION:0:20}"
```

Expected output:

```text
AYABeMud54rEoSpP-o6C
```

### 13.3 Export Run: Choose `PASSWORD`

This answers `SELECT_CHALLENGE` with the password method and captures the next response. If password validation succeeds, Cognito moves the flow to `SOFTWARE_TOKEN_MFA` and returns a replacement session for the MFA step.

```bash
export PASSWORD_CHALLENGE_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="$TEST_USERNAME",ANSWER="PASSWORD",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")

echo "$PASSWORD_CHALLENGE_RESPONSE" | jq
```

Expected output:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>",
  "ChallengeParameters": {
    "FRIENDLY_DEVICE_NAME": "Chewbacca CLI",
    "USER_ID_FOR_SRP": "chewbacca"
  }
}
```

Export the new session:

```bash
export SESSION=$(echo "$PASSWORD_CHALLENGE_RESPONSE" | jq -r '.Session')
```

### 13.4 Export Run: Respond To `SOFTWARE_TOKEN_MFA`

Get a fresh code from the authenticator app:

```bash
export TOTP_CODE="123456"
```

Respond to the MFA challenge:

This command completes the exported challenge chain. It sends the current TOTP code with the latest `Session`; when Cognito accepts the MFA code, the response changes from another challenge to `AuthenticationResult`.

```bash
export MFA_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="$TEST_USERNAME",SOFTWARE_TOKEN_MFA_CODE="$TOTP_CODE",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")

echo "$MFA_RESPONSE" | jq
```

Expected output:

```json
{
  "ChallengeParameters": {},
  "AuthenticationResult": {
    "AccessToken": "eyJraWQiOiJNek1LXC8yZzgz...<ACCESS_TOKEN_PAYLOAD>...<ACCESS_TOKEN_SIGNATURE>",
    "ExpiresIn": 900,
    "TokenType": "Bearer",
    "RefreshToken": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...<REFRESH_TOKEN>",
    "IdToken": "eyJraWQiOiJnVkkrSDRcL0Ja...eyJ0b2tlbl91c2UiOiJpZCIsImVtYWlsIjoiY2hld2JhY2NhQGV4YW1wbGUuY29tIn0...<ID_TOKEN_SIGNATURE>"
  }
}
```

Export tokens:

```bash
export ACCESS_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.AccessToken')
export ID_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.IdToken')
export REFRESH_TOKEN=$(echo "$MFA_RESPONSE" | jq -r '.AuthenticationResult.RefreshToken')

echo "${ACCESS_TOKEN:0:24}"
echo "${ID_TOKEN:0:24}"
echo "${REFRESH_TOKEN:0:24}"
```

Expected output:

```text
eyJraWQiOiJNek1LXC8yZzgz
eyJraWQiOiJnVkkrSDRcL0Ja
eyJjdHkiOiJKV1QiLCJlbmMi
```

> [!IMPORTANT]
> Access tokens expire after 15 minutes in this lab. If API Gateway later returns `{"message":"The incoming token has expired"}` or a `401`, rerun the export-driven authentication flow and retry with a fresh `ACCESS_TOKEN`.

## 14. Token Use

| Token | What it represents | Use in this lab |
| --- | --- | --- |
| Access token | Permission to call APIs | Use with API Gateway JWT authorizer |
| ID token | User identity/profile claims | Useful for inspecting user identity |
| Refresh token | Used to request new tokens | Keep private; do not send to API Gateway |

For API testing, use:

```bash
Authorization: Bearer $ACCESS_TOKEN
```

## 15. Add the Cognito JWT Authorizer

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

Validation:

```bash
aws apigatewayv2 get-authorizer \
  --api-id "$API_ID" \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

## 16. Test Protected API Routes

Test without a token:

This request intentionally omits the `Authorization` header. API Gateway should reject it at the JWT authorizer layer before the Lambda function runs, which confirms the route is protected.

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected:

```text
HTTP/2 401
content-type: application/json
...

{"message":"Unauthorized"}
```

Manual Check: test the Jedi route with the access token copied from **12.5 Manual Check: Respond To `SOFTWARE_TOKEN_MFA`**. Get `<API_ENDPOINT>` from the HTTP API stage URL.

This request sends the Cognito access token as a bearer token. HTTP API JWT authorizers validate the token issuer, audience, signature, and expiration before forwarding the request to Lambda.

```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "<API_ENDPOINT>/prod/jedi?name=Chewbacca"
```

Expected output:

```text
HTTP/2 200
...
```

Export Run: test the Jedi route with the exported access token:

This is the repeatable version of the same authorization test. The token comes from the exported MFA response, so rerunning the export-driven auth flow refreshes the value used by `curl`.

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected output:

```text
HTTP/2 200
...
```

> [!NOTE]
> If the response says `The incoming token has expired`, do not chase the Lambda first. API Gateway rejected the request before invocation. Return to **Step 13**, complete the export-driven authentication run again, and retry with the new `ACCESS_TOKEN`.

Export Run: test the Sith route:

This checks that the same authorizer behavior is attached consistently to the second protected route, not just to `/jedi`.

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected output:

```text
HTTP/2 200
...
```

Validation:

- Missing token returns `401`.
- Valid token returns `200`.
- Lambda logs appear only when authorization succeeds.

## 17. Direct Flow Shortcut

After MFA is enabled, `USER_PASSWORD_AUTH` skips `SELECT_CHALLENGE` and goes straight to password validation, then MFA.

Use this shortcut only after the manual learning pass. It is the same `initiate-auth` API, but with `USER_PASSWORD_AUTH` instead of `USER_AUTH`; that means the password is submitted immediately and Cognito can respond directly with the MFA challenge.

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
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>",
  "ChallengeParameters": {
    "FRIENDLY_DEVICE_NAME": "Chewbacca CLI",
    "USER_ID_FOR_SRP": "chewbacca"
  }
}
```

This is simpler for CLI testing, but it does not teach the `SELECT_CHALLENGE` negotiation step.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unable to verify secret hash` | Wrong username, client ID, client secret, or copied hash | Regenerate `SECRET_HASH` with the exact same username used in the auth request |
| `InvalidParameterException` for `USER_AUTH` | App client does not allow `ALLOW_USER_AUTH` or region/account does not support choice-based auth | Recreate/update app client with `ALLOW_USER_AUTH`; use `USER_PASSWORD_AUTH` if unavailable |
| `Invalid session due to a mismatched auth flow` | The `Session` came from the wrong auth flow, an older challenge chain, another app client, or another user | Restart from `initiate-auth --auth-flow USER_AUTH`, copy the fresh `SELECT_CHALLENGE` session, then use the new MFA session returned by the password step |
| `NotAuthorizedException` | Wrong password, stale session, wrong secret hash, or expired MFA step | Start the flow again from `initiate-auth` |
| `CodeMismatchException` | MFA code expired or copied incorrectly | Wait for a fresh authenticator code |
| `{"message":"The incoming token has expired"}` | Access token expired before the protected route test | Re-run the auth flow and export a fresh `ACCESS_TOKEN` |
| API returns `401` | Missing token, expired token, wrong issuer, wrong audience/client ID | Re-run the MFA flow and export a fresh `ACCESS_TOKEN` |
| API returns `500` | Lambda integration or function error | Check CloudWatch logs for the Lambda |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid JWTs before Lambda runs |

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

* [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
* [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
* [API Gateway HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
* [Lambda proxy integrations for HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)

### AWS CLI Command References

Every AWS CLI command used in this runbook is linked below to the direct AWS command reference page.

| Command | AWS CLI reference |
| --- | --- |
| `aws sts get-caller-identity` | [sts get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html) |
| `aws iam create-role` | [iam create-role](https://docs.aws.amazon.com/cli/latest/reference/iam/create-role.html) |
| `aws iam attach-role-policy` | [iam attach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/attach-role-policy.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |
| `aws iam detach-role-policy` | [iam detach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/detach-role-policy.html) |
| `aws iam delete-role` | [iam delete-role](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-role.html) |
| `aws lambda create-function` | [lambda create-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/create-function.html) |
| `aws lambda get-function` | [lambda get-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function.html) |
| `aws lambda invoke` | [lambda invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html) |
| `aws lambda add-permission` | [lambda add-permission](https://docs.aws.amazon.com/cli/latest/reference/lambda/add-permission.html) |
| `aws lambda delete-function` | [lambda delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html) |
| `aws logs delete-log-group` | [logs delete-log-group](https://docs.aws.amazon.com/cli/latest/reference/logs/delete-log-group.html) |
| `aws apigatewayv2 create-api` | [apigatewayv2 create-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-api.html) |
| `aws apigatewayv2 get-api` | [apigatewayv2 get-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-api.html) |
| `aws apigatewayv2 create-integration` | [apigatewayv2 create-integration](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-integration.html) |
| `aws apigatewayv2 create-route` | [apigatewayv2 create-route](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-route.html) |
| `aws apigatewayv2 create-stage` | [apigatewayv2 create-stage](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-stage.html) |
| `aws apigatewayv2 create-authorizer` | [apigatewayv2 create-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-authorizer.html) |
| `aws apigatewayv2 get-routes` | [apigatewayv2 get-routes](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-routes.html) |
| `aws apigatewayv2 update-route` | [apigatewayv2 update-route](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/update-route.html) |
| `aws apigatewayv2 get-authorizer` | [apigatewayv2 get-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/get-authorizer.html) |
| `aws apigatewayv2 delete-api` | [apigatewayv2 delete-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/delete-api.html) |
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
| `aws cognito-idp delete-user-pool` | [cognito-idp delete-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/delete-user-pool.html) |
| `aws cognito-idp describe-user-pool` | [cognito-idp describe-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/describe-user-pool.html) |

## Lab Teardown

Run this section when you are finished with the HTTP API lab and want to remove the AWS resources created during the walkthrough.

> [!WARNING]
> These commands delete the lab API, Lambda functions, Cognito user pool, CloudWatch log groups, and IAM role. Confirm you are using the HTTP API lab variables before running teardown.

Confirm the active lab values:

```bash
echo "$AWS_REGION"
echo "$PROJECT_NAME"
echo "$API_ID"
echo "$USER_POOL_ID"
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
echo "$LAMBDA_ROLE_NAME"
```

Delete the HTTP API. This removes its routes, integrations, stages, and authorizer:

```bash
aws apigatewayv2 delete-api \
  --api-id "$API_ID" \
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

Delete the Lambda CloudWatch log groups:

```bash
aws logs delete-log-group \
  --log-group-name "/aws/lambda/${JEDI_FUNCTION}" \
  --region "$AWS_REGION"

aws logs delete-log-group \
  --log-group-name "/aws/lambda/${SITH_FUNCTION}" \
  --region "$AWS_REGION"
```

Delete the Cognito user pool. This also removes the app client, test user, MFA configuration, and issued-token context for the lab:

```bash
aws cognito-idp delete-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"
```

Detach the managed policy and delete the Lambda execution role:

```bash
aws iam detach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role \
  --role-name "$LAMBDA_ROLE_NAME"
```

Validate teardown:

```bash
aws apigatewayv2 get-api \
  --api-id "$API_ID" \
  --region "$AWS_REGION"

aws cognito-idp describe-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"

aws lambda get-function \
  --function-name "$JEDI_FUNCTION" \
  --region "$AWS_REGION"
```

Expected result: each validation command should return a not-found style error after teardown.

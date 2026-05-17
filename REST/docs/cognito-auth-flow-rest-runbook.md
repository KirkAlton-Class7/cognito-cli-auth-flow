# Chewbacca Cognito CLI Auth Flow Lab - REST Version

REST API implementation of the Chewbacca Cognito CLI auth-flow lab.<br>
View the HTTP API version [here](../../HTTPS/README.md) if you prefer that implementation.<br><br>

This lab keeps the same authentication story as the HTTP API version. Build the infrastructure in the AWS Console, then use the CLI for the Cognito challenge flow, manual token inspection, exported-token reuse, and protected route tests:

```text
Chewbacca CLI user
  -> Cognito User Pool
  -> USER_AUTH / SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> JWT tokens
  -> API Gateway REST API
  -> Cognito User Pool Authorizer
  -> Lambda
  -> CloudWatch Logs
```

The implementation difference is API Gateway. REST APIs do not use the HTTP API JWT authorizer command set. For this lab, use a native **Cognito User Pool authorizer** on the REST API methods.

> [!NOTE]
> No custom authenticator Lambda is needed for the protected Jedi and Sith routes. API Gateway REST API can validate Cognito user-pool tokens directly with a Cognito authorizer. A Lambda authorizer would be useful for custom token logic, non-Cognito identity providers, or policy decisions that Cognito scopes alone cannot express.

## Build Mode

Use the **AWS Console** to create infrastructure:

```text
IAM role
Lambda functions
REST API
REST resources and methods
Lambda proxy integrations
Cognito user pool
Cognito app client
Chewbacca test user
REST API Cognito User Pool authorizer
prod deployment
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

| Route | Runtime | Theme role | Protection |
| --- | --- | --- | --- |
| `/prod/jedi` | Python | Jedi Council response path | Cognito User Pool authorizer |
| `/prod/sith` | Node.js | Sith response path | Cognito User Pool authorizer |

## Source Material

| Source | Purpose |
| --- | --- |
| [`../../shared/lambda-code`](../../shared/lambda-code/) | Shared Jedi and Sith Lambda functions |
| [`../../shared/scripts/secret_hash.py`](../../shared/scripts/secret_hash.py) | Helper script for Cognito app clients with a client secret |
| Original class notes | Recovered `USER_AUTH`, challenge selection, MFA, and token-handling workflow |
| Original Lesson B Lambda lab | Simple API Gateway + Lambda pattern that shaped the Jedi/Sith route handlers |

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
export LAB_REPO="$HOME/cognito-cli-auth-flow"
cd "$LAB_REPO"
```

## 1. Record And Export Lab Values For CLI Testing

Create the infrastructure in the AWS Console using these names, then export the same values in your terminal before running the authentication flow. Use a REST-specific project name so this version can run beside the HTTP API version.

```bash
export AWS_REGION="us-west-2"
export PROJECT_NAME="chewbacca-auth-rest"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"

export API_NAME="${PROJECT_NAME}-api"
export USER_POOL_NAME="${PROJECT_NAME}-users"
export USER_POOL_CLIENT_NAME="${PROJECT_NAME}-cli-client"
export AUTHORIZER_NAME="${PROJECT_NAME}-cognito-authorizer"

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

Package the shared Jedi and Sith functions.

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
| Jedi function name | Lambda function overview | `chewbacca-auth-rest-jedi-python` |
| Jedi function ARN | Lambda function overview -> **Function ARN** | `<JEDI_FUNCTION_ARN>` |
| Sith function name | Lambda function overview | `chewbacca-auth-rest-sith-node` |
| Sith function ARN | Lambda function overview -> **Function ARN** | `<SITH_FUNCTION_ARN>` |
| Lambda execution role | Lambda function configuration -> **Permissions** | `chewbacca-auth-rest-lambda-basic-role` |

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
  /tmp/chewbacca-rest-jedi-response.json \
  --region "$AWS_REGION"

jq . /tmp/chewbacca-rest-jedi-response.json
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
  /tmp/chewbacca-rest-sith-response.json \
  --region "$AWS_REGION"

jq . /tmp/chewbacca-rest-sith-response.json
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

## 6. Create the REST API

Console path: **API Gateway** -> **Create API** -> **REST API** -> **Build** -> **New API** -> API name from `API_NAME` -> endpoint type **Regional**.

> [!IMPORTANT]
> Keep these values handy for resources, methods, deployment, and teardown:

| Parameter | Console Location | Value |
| --- | --- | --- |
| REST API name | API Gateway REST API details | `chewbacca-auth-rest-api` |
| REST API ID | API Gateway REST API details | `<REST_API_ID>` |
| Root resource ID | API Gateway resources view or CLI lookup | `<ROOT_RESOURCE_ID>` |
| Endpoint type | API settings | `Regional` |

Equivalent CLI reference:

```bash
export REST_API_ID=$(aws apigateway create-rest-api \
  --name "$API_NAME" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text \
  --region "$AWS_REGION")
```

Export the root resource ID:

```bash
export ROOT_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --query "items[?path=='/'].id | [0]" \
  --output text \
  --region "$AWS_REGION")
```

Create the Jedi and Sith resources:

```bash
export JEDI_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id "$REST_API_ID" \
  --parent-id "$ROOT_RESOURCE_ID" \
  --path-part jedi \
  --query 'id' \
  --output text \
  --region "$AWS_REGION")

export SITH_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id "$REST_API_ID" \
  --parent-id "$ROOT_RESOURCE_ID" \
  --path-part sith \
  --query 'id' \
  --output text \
  --region "$AWS_REGION")
```

Validation:

```bash
echo "$REST_API_ID"
echo "$JEDI_RESOURCE_ID"
echo "$SITH_RESOURCE_ID"
```

## 7. Add REST Methods And Lambda Proxy Integrations

Create public `GET` methods first so you can prove the API and Lambda routing work before adding Cognito.

In the console, create `/jedi` and `/sith` resources, add `GET` methods, use Lambda proxy integration, select the matching Lambda function, and deploy to the `prod` stage.

> [!IMPORTANT]
> Keep these values handy for method authorization and route testing:

| Parameter | Console Location | Value |
| --- | --- | --- |
| Jedi resource path | API Gateway resources | `/jedi` |
| Jedi resource ID | API Gateway resources or CLI lookup | `<JEDI_RESOURCE_ID>` |
| Sith resource path | API Gateway resources | `/sith` |
| Sith resource ID | API Gateway resources or CLI lookup | `<SITH_RESOURCE_ID>` |
| Deployment stage | API Gateway stages | `prod` |
| Invoke URL / endpoint | Stage details | `<API_ENDPOINT>` |

Equivalent CLI reference:

```bash
aws apigateway put-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$JEDI_RESOURCE_ID" \
  --http-method GET \
  --authorization-type NONE \
  --region "$AWS_REGION"

aws apigateway put-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$SITH_RESOURCE_ID" \
  --http-method GET \
  --authorization-type NONE \
  --region "$AWS_REGION"
```

Add Lambda proxy integrations:

```bash
aws apigateway put-integration \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$JEDI_RESOURCE_ID" \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${JEDI_FUNCTION_ARN}/invocations" \
  --region "$AWS_REGION"

aws apigateway put-integration \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$SITH_RESOURCE_ID" \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${SITH_FUNCTION_ARN}/invocations" \
  --region "$AWS_REGION"
```

Allow API Gateway to invoke Lambda:

```bash
aws lambda add-permission \
  --function-name "$JEDI_FUNCTION" \
  --statement-id "${REST_API_ID}-jedi-invoke" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${REST_API_ID}/*/GET/jedi" \
  --region "$AWS_REGION"

aws lambda add-permission \
  --function-name "$SITH_FUNCTION" \
  --statement-id "${REST_API_ID}-sith-invoke" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${REST_API_ID}/*/GET/sith" \
  --region "$AWS_REGION"
```

Deploy the public baseline:

```bash
aws apigateway create-deployment \
  --rest-api-id "$REST_API_ID" \
  --stage-name prod \
  --description "Public baseline before Cognito authorizer" \
  --region "$AWS_REGION"
```

Export the REST endpoint:

```bash
export API_ENDPOINT="https://${REST_API_ID}.execute-api.${AWS_REGION}.amazonaws.com"
```

## 8. Test The Public REST API Before Auth

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
- CloudWatch logs show REST API Lambda proxy event payloads.
- The event includes `queryStringParameters.name`.

## 9. Create the Cognito User Pool

Create the user pool first with MFA off. Cognito requires SMS configuration when MFA is set to optional during `create-user-pool`, so software-token MFA is enabled after the pool exists.

Console path: **Amazon Cognito** -> **User pools** -> **Create user pool**. Use email sign-in and the password policy shown below. Leave MFA off during initial pool creation, then enable software-token MFA after the pool exists.

> [!IMPORTANT]
> Keep these values handy for app client setup, authorizer setup, and CLI authentication:

| Parameter | Console Location | Value |
| --- | --- | --- |
| User pool name | Cognito user pool details | `chewbacca-auth-rest-users` |
| User pool ID | Cognito user pool details | `<USER_POOL_ID>` |
| User pool ARN | Cognito user pool details | `<USER_POOL_ARN>` |
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

Export the issuer and user pool ARN:

```bash
export COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"
export USER_POOL_ARN="arn:aws:cognito-idp:${AWS_REGION}:${AWS_ACCOUNT_ID}:userpool/${USER_POOL_ID}"
```

Validation:

```bash
echo "$USER_POOL_ID"
echo "$COGNITO_ISSUER"
echo "$USER_POOL_ARN"
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
> The barebones REST route test uses the ID token when no method-level OAuth scopes are configured. A 15-minute ID token makes expiration behavior easy to observe without waiting through a long default session.

> [!IMPORTANT]
> Keep these values handy for `SECRET_HASH`, manual authentication, and the export-driven run:

| Parameter | Console Location | Value |
| --- | --- | --- |
| App client name | Cognito app client details | `chewbacca-auth-rest-cli-client` |
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
| `<ID_TOKEN>` | `AuthenticationResult.IdToken` from the final MFA response |

> [!IMPORTANT]
> Complete this manual run before using the export-driven run. Copying the two different `Session` values by hand is what makes the Cognito challenge sequence visible.

### 12.1 Manual Check: Generate `SECRET_HASH`

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

Copy that output and use it as `<SECRET_HASH>` in the next manual commands.

### 12.2 Manual Check: Bootstrap TOTP MFA

Authenticate once with direct password auth. MFA is optional at this point, so Cognito should return temporary tokens.

> [!NOTE]
> Run this bootstrap step only for a fresh test user that has not enrolled an authenticator app yet. If MFA is already enrolled, skip to **12.3 Manual Check: Start `USER_AUTH`**.

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
  "AuthenticationResult": {
    "AccessToken": "<TEMP_ACCESS_TOKEN>",
    "IdToken": "<ID_TOKEN>",
    "RefreshToken": "<REFRESH_TOKEN>",
    "TokenType": "Bearer",
    "ExpiresIn": 900
  }
}
```

Use the temporary access token to request a software-token secret:

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

Add `<TOTP_SECRET>` to your authenticator app as a manual setup key. Then verify the current six-digit code:

```bash
aws cognito-idp verify-software-token \
  --access-token "<TEMP_ACCESS_TOKEN>" \
  --user-code "<MFA_CODE>" \
  --friendly-device-name "Chewbacca CLI REST" \
  --region "<REGION>" | jq
```

Expected output:

```json
{
  "Status": "SUCCESS"
}
```

Set software token MFA as preferred:

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
  "AvailableChallenges": [
    "PASSWORD",
    "PASSWORD_SRP"
  ],
  "Session": "<SELECT_CHALLENGE_SESSION>"
}
```

Copy `<SELECT_CHALLENGE_SESSION>` into the next command.

### 12.4 Manual Check: Choose `PASSWORD`

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
  "Session": "<SOFTWARE_TOKEN_MFA_SESSION>"
}
```

Copy `<SOFTWARE_TOKEN_MFA_SESSION>` into the next command.

### 12.5 Manual Check: Respond To `SOFTWARE_TOKEN_MFA`

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
  "AuthenticationResult": {
    "AccessToken": "<ACCESS_TOKEN>",
    "IdToken": "<ID_TOKEN>",
    "RefreshToken": "<REFRESH_TOKEN>",
    "TokenType": "Bearer",
    "ExpiresIn": 900
  }
}
```

For the no-scope REST API route test, copy `<ID_TOKEN>`.

> [!WARNING]
> Cognito challenge sessions are short-lived. If too much time passes between manual commands, restart from **12.3 Manual Check: Start `USER_AUTH`**.

## 13. Export-Driven Authentication Run

After completing the manual run, repeat the same authentication flow with shell exports. This pass is for speed and repeatability.

### 13.1 Export `SECRET_HASH`

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

Expected output:

```text
<first-20-characters-of-session>
```

### 13.3 Export Run: Choose `PASSWORD`

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
  "Session": "..."
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
  "AuthenticationResult": {
    "AccessToken": "...",
    "IdToken": "...",
    "RefreshToken": "...",
    "TokenType": "Bearer",
    "ExpiresIn": 900
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
<first-24-characters-of-access-token>
<first-24-characters-of-id-token>
<first-24-characters-of-refresh-token>
```

> [!IMPORTANT]
> ID tokens expire after 15 minutes in this lab. If API Gateway later returns `{"message":"The incoming token has expired"}` or a `401`, rerun the export-driven authentication flow and retry with a fresh `ID_TOKEN`.

## 14. Token Use

| Token | What it represents | Use in this lab |
| --- | --- | --- |
| Access token | Permission to call APIs | Use when REST methods require OAuth scopes |
| ID token | User identity/profile claims | Use for this barebones REST authorizer lab with no method scopes configured |
| Refresh token | Used to request new tokens | Keep private; do not send to API Gateway |

For this REST lab, use:

```bash
Authorization: Bearer $ID_TOKEN
```

> [!NOTE]
> REST API Cognito authorizers can validate Cognito user-pool tokens directly. With no authorization scopes configured, API Gateway treats the supplied token as an identity token. If you later configure method-level authorization scopes, use the access token and make sure the requested token includes the required scopes.

## 15. Add the REST API Cognito Authorizer

Console path: open the REST API -> **Authorizers** -> **Create authorizer**. Use a Cognito User Pool authorizer with token source `Authorization`, then attach it to the `GET /jedi` and `GET /sith` methods.

> [!IMPORTANT]
> Keep these values handy for validation and troubleshooting:

| Parameter | Console Location | Value |
| --- | --- | --- |
| Authorizer name | REST API authorizer details | `chewbacca-auth-rest-cognito-authorizer` |
| Authorizer ID | REST API authorizer details | `<COGNITO_AUTHORIZER_ID>` |
| Cognito provider ARN | Cognito user pool details | `<USER_POOL_ARN>` |
| Token source | Authorizer token source | `Authorization` |
| Protected methods | REST API resources and methods | `GET /jedi`, `GET /sith` |

Equivalent CLI reference:

```bash
export COGNITO_AUTHORIZER_ID=$(aws apigateway create-authorizer \
  --rest-api-id "$REST_API_ID" \
  --name "$AUTHORIZER_NAME" \
  --type COGNITO_USER_POOLS \
  --provider-arns "$USER_POOL_ARN" \
  --identity-source method.request.header.Authorization \
  --query 'id' \
  --output text \
  --region "$AWS_REGION")
```

Attach the authorizer to both methods:

```bash
aws apigateway update-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$JEDI_RESOURCE_ID" \
  --http-method GET \
  --patch-operations \
    op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
    op=replace,path=/authorizerId,value="$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"

aws apigateway update-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$SITH_RESOURCE_ID" \
  --http-method GET \
  --patch-operations \
    op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
    op=replace,path=/authorizerId,value="$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

Redeploy the API after changing method authorization:

```bash
aws apigateway create-deployment \
  --rest-api-id "$REST_API_ID" \
  --stage-name prod \
  --description "Protected Jedi and Sith routes with Cognito authorizer" \
  --region "$AWS_REGION"
```

Validation:

```bash
aws apigateway get-authorizer \
  --rest-api-id "$REST_API_ID" \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

## 16. Test Protected REST API Routes

Test without a token:

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected:

```text
HTTP/2 401
```

Manual Check: test the Jedi route with the ID token copied from **12.5 Manual Check: Respond To `SOFTWARE_TOKEN_MFA`**. Get `<API_ENDPOINT>` from the REST API invoke URL.

```bash
curl -i \
  -H "Authorization: Bearer <ID_TOKEN>" \
  "<API_ENDPOINT>/prod/jedi?name=Chewbacca"
```

Expected output:

```text
HTTP/2 200
...
```

Export Run: test the Jedi route with the exported ID token:

```bash
curl -i \
  -H "Authorization: Bearer $ID_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected output:

```text
HTTP/2 200
...
```

> [!NOTE]
> If the response says `The incoming token has expired`, do not chase the Lambda first. API Gateway rejected the request before invocation. Return to **Step 13**, complete the export-driven authentication run again, and retry with the new `ID_TOKEN`.

Export Run: test the Sith route:

```bash
curl -i \
  -H "Authorization: Bearer $ID_TOKEN" \
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
| `{"message":"The incoming token has expired"}` | ID token expired before the protected route test | Re-run the auth flow and export a fresh `ID_TOKEN` |
| REST route stays public | Method authorization changed but API was not redeployed | Run `create-deployment` again for the `prod` stage |
| REST route returns `401` with token | Wrong user pool ARN, expired token, access token used without scopes, malformed Authorization header, or wrong API deployment | Use `ID_TOKEN` for the no-scope lab, confirm authorizer provider ARN, and redeploy |
| API returns `500` | Lambda integration or function error | Check CloudWatch logs for the Lambda |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid tokens before Lambda runs |

## Final Check

You have completed the REST lab when you can explain this flow without looking:

```text
SECRET_HASH proves the app client secret
USER_AUTH starts negotiation
SELECT_CHALLENGE lets the client choose PASSWORD
PASSWORD validates the primary factor
SOFTWARE_TOKEN_MFA validates the second factor
Cognito issues JWT tokens
REST API Cognito authorizer validates the ID token for no-scope methods
Lambda only runs after authorization succeeds
CloudWatch proves what actually happened
```

## References

* [AWS CLI `initiate-auth`](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html)
* [AWS CLI `respond-to-auth-challenge`](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html)
* [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
* [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
* [API Gateway REST API Cognito authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
* [REST API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)

## Lab Teardown

Run this section when you are finished with the REST API lab and want to remove the AWS resources created during the walkthrough.

> [!WARNING]
> These commands delete the lab API, Lambda functions, Cognito user pool, CloudWatch log groups, and IAM role. Confirm you are using the REST API lab variables before running teardown.

Confirm the active lab values:

```bash
echo "$AWS_REGION"
echo "$PROJECT_NAME"
echo "$REST_API_ID"
echo "$USER_POOL_ID"
echo "$JEDI_FUNCTION"
echo "$SITH_FUNCTION"
echo "$LAMBDA_ROLE_NAME"
```

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
aws apigateway get-rest-api \
  --rest-api-id "$REST_API_ID" \
  --region "$AWS_REGION"

aws cognito-idp describe-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$AWS_REGION"

aws lambda get-function \
  --function-name "$JEDI_FUNCTION" \
  --region "$AWS_REGION"
```

Expected result: each validation command should return a not-found style error after teardown.

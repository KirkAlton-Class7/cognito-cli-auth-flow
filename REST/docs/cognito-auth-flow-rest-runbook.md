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

Validation:

- Jedi Python returns a JSON body with `The Python Jedi Council accepts your request.`
- Sith Node returns a JSON body with `THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.`
- CloudWatch has log groups for both functions.

## 6. Create the REST API

Console path: **API Gateway** -> **Create API** -> **REST API** -> **Build** -> **New API** -> API name from `API_NAME` -> endpoint type **Regional**.

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

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show REST API Lambda proxy event payloads.
- The event includes `queryStringParameters.name`.

## 9. Create the Cognito User Pool

Create the user pool first with MFA off. Cognito requires SMS configuration when MFA is set to optional during `create-user-pool`, so software-token MFA is enabled after the pool exists.

Console path: **Amazon Cognito** -> **User pools** -> **Create user pool**. Use email sign-in and the password policy shown below. Leave MFA off during initial pool creation, then enable software-token MFA after the pool exists.

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

Console path: open the user pool -> **App clients** -> **Create app client**. Enable the auth flows shown below and generate a client secret.

Equivalent CLI reference:

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

Console path: open the user pool -> **Users** -> **Create user**. Use the username, email, and password values from the export block.

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

## 12. Generate the Cognito SECRET_HASH

`SECRET_HASH` proves the request knows the app client secret without sending the raw secret as the challenge answer.

```bash
cd "$LAB_REPO"
```

Manual check:

```bash
python3 shared/scripts/secret_hash.py \
  "$TEST_USERNAME" \
  "$CLIENT_ID" \
  "$CLIENT_SECRET"
```

Export path:

```bash
export SECRET_HASH=$(python3 shared/scripts/secret_hash.py \
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

> [!IMPORTANT]
> This temporary access token is only used to enroll MFA. If `associate-software-token`, `verify-software-token`, or `set-user-mfa-preference` fails because the token expired, re-run the `USER_PASSWORD_AUTH` command in this section and export a fresh `ACCESS_TOKEN`.

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
  --friendly-device-name "Chewbacca CLI REST" \
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

`USER_AUTH` starts with negotiation. Cognito asks which challenge you want to use.

### 14.1 Manual-First Pass

Run the first pass slowly. Do not export the response yet. Read the JSON, copy the `Session` value, and paste it into the next command.

```bash
aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION" | jq
```

Copy the `Session` value from the `SELECT_CHALLENGE` response.

```bash
aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="$TEST_USERNAME",ANSWER="PASSWORD",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --session "PASTE_SELECT_CHALLENGE_SESSION_HERE" \
  --region "$AWS_REGION" | jq
```

Copy the new `Session` value from the `SOFTWARE_TOKEN_MFA` response. Then paste a fresh authenticator code and the new session into the MFA response.

```bash
aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="$TEST_USERNAME",SOFTWARE_TOKEN_MFA_CODE="PASTE_CURRENT_MFA_CODE",SECRET_HASH="$SECRET_HASH" \
  --session "PASTE_SOFTWARE_TOKEN_MFA_SESSION_HERE" \
  --region "$AWS_REGION" | jq
```

The final response contains `AccessToken`, `IdToken`, and `RefreshToken`. For the no-scope REST API route test, copy the `IdToken`.

> [!TIP]
> This manual pass is the teaching pass. You should see Cognito issue one session for challenge selection, then a different session for MFA. After you see that flow, use the export-driven commands below to repeat it faster.

### 14.2 Export-Driven Pass

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

> [!WARNING]
> Cognito challenge sessions are short-lived. If you wait too long between `initiate-auth`, `SELECT_CHALLENGE`, and `SOFTWARE_TOKEN_MFA`, the session can expire. Start again from **Step 14** and replace `SESSION` with the new value.

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

> [!IMPORTANT]
> ID tokens and access tokens expire. If API Gateway later returns `{"message":"The incoming token has expired"}` or a `401`, the route and Lambda may still be correct. Re-run the auth flow, export a fresh `ID_TOKEN`, and retry the protected route.

## 17. Token Use

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

## 18. Add the REST API Cognito Authorizer

Console path: open the REST API -> **Authorizers** -> **Create authorizer**. Use a Cognito User Pool authorizer with token source `Authorization`, then attach it to the `GET /jedi` and `GET /sith` methods.

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

## 19. Test Protected REST API Routes

Test without a token:

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected:

```text
HTTP/2 401
```

Test the Jedi route with the Cognito ID token:

```bash
curl -i \
  -H "Authorization: Bearer $ID_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

> [!NOTE]
> If the response says `The incoming token has expired`, do not chase the Lambda first. API Gateway rejected the request before invocation. Return to **Step 14**, complete the challenge flow again, and retry with the new `ID_TOKEN`.

Manual token test:

```bash
curl -i \
  -H "Authorization: Bearer PASTE_ID_TOKEN_HERE" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Test the Sith route:

```bash
curl -i \
  -H "Authorization: Bearer $ID_TOKEN" \
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
| `{"message":"The incoming token has expired"}` | ID token expired before the protected route test | Re-run the auth flow and export a fresh `ID_TOKEN` |
| REST route stays public | Method authorization changed but API was not redeployed | Run `create-deployment` again for the `prod` stage |
| REST route returns `401` with token | Wrong user pool ARN, expired token, access token used without scopes, malformed Authorization header, or wrong API deployment | Use `ID_TOKEN` for the no-scope lab, confirm authorizer provider ARN, and redeploy |
| API returns `500` | Lambda integration or function error | Check CloudWatch logs for the Lambda |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid tokens before Lambda runs |

## Cleanup

Delete REST API:

```bash
aws apigateway delete-rest-api \
  --rest-api-id "$REST_API_ID" \
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

# Cognito Auth Flow - REST Lab - CLI

This lab teaches the REST version of the Cognito auth flow. You will build most resources with CLI commands when possible, and conceptual checkpoints will explain why each step matters.

This flow uses:

```text
Chewbacca test user
  -> Cognito User Pool
  -> default public app client for token helper scripts
  -> additional secret-bearing CLI app client for SECRET_HASH
  -> USER_AUTH / SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> access token with aws.cognito.signin.user.admin scope
  -> API Gateway REST API Cognito authorizer
  -> protected /prod/jedi and /prod/sith Lambda routes
```

> [!IMPORTANT]
> This version protects REST methods with an authorization scope. Once `aws.cognito.signin.user.admin` is configured on the API methods, use the Cognito **access token** for protected route tests. Do not use the ID token for the scoped route test.

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

## 1. Record And Export Runbook Values

Use a REST-specific project name so the REST and HTTP API versions can exist in the same account.

```bash
export AWS_REGION="us-east-1"
export PROJECT_NAME="chewbacca-auth-rest"

export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"

export PYTHON_LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-python-role"
export NODE_LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-node-role"

export API_NAME="${PROJECT_NAME}-api"
export USER_POOL_NAME="${PROJECT_NAME}-users"
export DEFAULT_APP_CLIENT_NAME="${PROJECT_NAME}-users"
export USER_POOL_CLIENT_NAME="${PROJECT_NAME}-cli-client"
export AUTHORIZER_NAME="${PROJECT_NAME}-cognito-authorizer"
export REQUIRED_AUTH_SCOPE="aws.cognito.signin.user.admin"

export TEST_USERNAME="chewbacca"
export TEST_EMAIL="chewbacca@example.com"
export TEST_PASSWORD="Wookiee#2026!"
export TEMP_PASSWORD="Wookiee#TEMP1!"
```

> [!IMPORTANT]
> `TEST_EMAIL` must be an active email account you can access for identity verification and managed-login testing. `TEST_USERNAME`, `TEST_PASSWORD`, and `TEMP_PASSWORD` can be customized, but keep the exported values consistent throughout the runbook.

Get the account ID:

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

Validate every starting value before building:

```bash
echo "AWS_REGION=$AWS_REGION"
echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID"
echo "PROJECT_NAME=$PROJECT_NAME"
echo
echo "JEDI_FUNCTION=$JEDI_FUNCTION"
echo "SITH_FUNCTION=$SITH_FUNCTION"
echo "PYTHON_LAMBDA_ROLE_NAME=$PYTHON_LAMBDA_ROLE_NAME"
echo "NODE_LAMBDA_ROLE_NAME=$NODE_LAMBDA_ROLE_NAME"
echo
echo "API_NAME=$API_NAME"
echo "USER_POOL_NAME=$USER_POOL_NAME"
echo "DEFAULT_APP_CLIENT_NAME=$DEFAULT_APP_CLIENT_NAME"
echo "USER_POOL_CLIENT_NAME=$USER_POOL_CLIENT_NAME"
echo "AUTHORIZER_NAME=$AUTHORIZER_NAME"
echo "REQUIRED_AUTH_SCOPE=$REQUIRED_AUTH_SCOPE"
echo
echo "TEST_USERNAME=$TEST_USERNAME"
echo "TEST_EMAIL=$TEST_EMAIL"
echo "TEST_PASSWORD=$TEST_PASSWORD"
echo "TEMP_PASSWORD=$TEMP_PASSWORD"
```

> [!CAUTION]
> Stop here if any value is wrong. Later commands reuse these exports for ARNs, Lambda permissions, Cognito clients, and REST method authorization.

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

![Package Lambda ZIP files](/assets/temp/104-3-package-lambdas.png)

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

![Export function ARNs and validate](/assets/temp/120-4-export-function-arns-and-validate.png)

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

![Jedi Python invoke success](/assets/temp/028-5-invoke-jedi-python-success.png)

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

![Sith Node invoke success](/assets/temp/024-5-invoke-sith-node-success.png)

## 6. Create The REST API And Resources

### Commands

Create the REST API:

```bash
export REST_API_ID=$(aws apigateway create-rest-api \
  --name "$API_NAME" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text \
  --region "$AWS_REGION")
```

Export the root resource:

```bash
export ROOT_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --query "items[?path=='/'].id | [0]" \
  --output text \
  --region "$AWS_REGION")
```

Create the REST resources:

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

If you created the API through clickops, open **API settings** and export the API ID:

```bash
export REST_API_ID="<REST_API_ID_FROM_CONSOLE>"
export API_ENDPOINT="https://${REST_API_ID}.execute-api.${AWS_REGION}.amazonaws.com"
```

If you created the `/jedi` and `/sith` resources through clickops, copy the resource IDs from API Gateway and export them directly:

```bash
export ROOT_RESOURCE_ID="<ROOT_RESOURCE_ID_FROM_CONSOLE>"
export JEDI_RESOURCE_ID="<JEDI_RESOURCE_ID_FROM_CONSOLE>"
export SITH_RESOURCE_ID="<SITH_RESOURCE_ID_FROM_CONSOLE>"
```

Validation:

```bash
echo "$REST_API_ID"
echo "$ROOT_RESOURCE_ID"
echo "$JEDI_RESOURCE_ID"
echo "$SITH_RESOURCE_ID"
echo "$API_ENDPOINT"
```

## 7. Add REST Methods And Lambda Proxy Integrations

Create public `GET` methods before adding Cognito. This proves routing works before authorization.

### Commands

Create the public `GET` methods:

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

Deploy the public API and export the endpoint:

```bash
aws apigateway create-deployment \
  --rest-api-id "$REST_API_ID" \
  --stage-name prod \
  --description "Public Jedi and Sith baseline before Cognito authorizer" \
  --region "$AWS_REGION"

export API_ENDPOINT="https://${REST_API_ID}.execute-api.${AWS_REGION}.amazonaws.com"
```

## 8. Test Unprotected REST Paths Without A Token

These tests should work before the authorizer is attached.

Test the Python route:

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Test the Node route:

```bash
curl -i "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected:

```text
HTTP/2 200
```

Both unprotected route tests:

![Unprotected API path tests](/assets/temp/015-test-api-paths-without-authorizer-png.png)

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show Lambda proxy event payloads.
- If either request fails now, fix routing before adding Cognito.

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
| Default `chewbacca-auth-rest-users` client | No secret | Managed login and token helper scripts |
| Additional `chewbacca-auth-rest-cli-client` client | Secret | Manual CLI flow with `SECRET_HASH` |

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

This runbook creates an additional app client with a client secret so you can work directly with `SECRET_HASH` and understand how Cognito generates and validates it.

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

![Login page error before style setup](/assets/temp/044-10-login-page-error.png)

![Select create style](/assets/temp/116-10-select-create-style.png)

4. Select `chewbacca-auth-rest-cli-client`.

![Select CLI app client for login style](/assets/temp/067-10-login-style-select-cli-app-client.png)

5. Click **Create**.

![Login style creation success](/assets/temp/017-10-login-style-cli-app-creation-success.png)

6. Click the **Assigned app client** to return to the app client page.
7. Click **View login page**.

![Select view login page](/assets/temp/094-10-cli-app-client-select-view-login-page.png)

8. Confirm the CLI app client login page opens.

![CLI app client login page](/assets/temp/095-10-cli-app-client-login-page.png)

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

## 13. Add The REST API Cognito Authorizer

### Commands

Create the authorizer:

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

Attach the authorizer and required scope to `GET /jedi`:

```bash
aws apigateway update-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$JEDI_RESOURCE_ID" \
  --http-method GET \
  --patch-operations \
    op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
    op=replace,path=/authorizerId,value="$COGNITO_AUTHORIZER_ID" \
    op=replace,path=/authorizationScopes,value="$REQUIRED_AUTH_SCOPE" \
  --region "$AWS_REGION"
```

Attach the authorizer and required scope to `GET /sith`:

```bash
aws apigateway update-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$SITH_RESOURCE_ID" \
  --http-method GET \
  --patch-operations \
    op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
    op=replace,path=/authorizerId,value="$COGNITO_AUTHORIZER_ID" \
    op=replace,path=/authorizationScopes,value="$REQUIRED_AUTH_SCOPE" \
  --region "$AWS_REGION"
```

Redeploy the API:

```bash
aws apigateway create-deployment \
  --rest-api-id "$REST_API_ID" \
  --stage-name prod \
  --description "Protected Jedi and Sith routes with Cognito authorizer and scope" \
  --region "$AWS_REGION"
```

Validate the authorizer:
```bash
aws apigateway get-authorizer \
  --rest-api-id "$REST_API_ID" \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

![Validate authorizer](/assets/temp/006-12-cli-validate-authroizer.png)

## 14. Test Authorizer Enforcement Without A Token

Call the protected routes with no `Authorization` header:

```bash
curl -i "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

```bash
curl -i "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected:

```text
HTTP/2 401
{"message":"Unauthorized"}
```

Unauthorized response confirmation:

![Authorizer enforcement without token](/assets/temp/119-13-test-authorizer-enforcement-no-token.png)

Validation:

- Missing token returns `401`.
- Lambda does not run.
- If the route still returns `200`, redeploy the API or recheck method authorization settings.

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

![Generate secret hash manually](/assets/temp/050-14-cli-generate-secret-hash.png)

Secret hash export confirmation:

![Export secret hash](/assets/temp/085-screenshot-2026-06-04-at-11-39-46-am.png)

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

![Initial TOTP MFA setup attempt](/assets/temp/060-14-1initial-totp-mfa.png)

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

![Associate software token](/assets/temp/019-1-2-associate-software-token.png)

Copy `SecretCode` into your authenticator app to store the shared secret and generate TOTP codes for future authentication.

![Add Secret Code to Authenticator](/assets/temp/115-11-desktop-authenticator-setup.png)

![TOTP Codes in Authenticator](/assets/temp/101-11-desktop-authenticator-code-generated.png)


Verify the software token with a valid TOTP code from your authenticator app:

```bash
export TOTP_CODE="<FRESH_6_DIGIT_CODE>"

aws cognito-idp verify-software-token \
  --access-token "$TEMP_ACCESS_TOKEN" \
  --user-code "$TOTP_CODE" \
  --friendly-device-name "Chewbacca CLI REST" \
  --region "$AWS_REGION" | jq
```

Expected:

```json
{
  "Status": "SUCCESS"
}
```

Verify software token:

![Verify software token](/assets/temp/114-1-3-verify-software-token.png)

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

![View CLI app client login page](/assets/temp/076-11-cli-app-client-view-login-page.png)

2. Sign in with username `chewbacca` and the temporary password.

![CLI app sign-in](/assets/temp/011-11-cli-app-signin.png)

![CLI app sign-in screen](/assets/temp/096-11-cli-app-sign-in.png)

3. Change the temporary password to the permanent password exported earlier.

![CLI app change password](/assets/temp/052-11-cli-app-change-password.png)

If the challenge session expires while you are learning the flow, restart the hosted login sequence and continue with a newly generated authenticator code.

![Session expired warning](/assets/temp/110-11-session-expired-error.png)

4. Continue to authenticator app setup.

![Set up authenticator app](/assets/temp/025-11-set-up-authenticator-app.png)

5. Scan the QR code or click **Show secret key** and add the key manually to your authenticator app.

![Desktop authenticator setup](/assets/temp/115-11-desktop-authenticator-setup.png)

6. Use a valid TOTP code from your authenticator app.

![Desktop authenticator code generated](/assets/temp/101-11-desktop-authenticator-code-generated.png)

7. Complete sign-in.

![Successful sign-in](/assets/temp/034-11-successful-sign-in.png)

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

![Start USER_AUTH and receive SELECT_CHALLENGE](/assets/temp/106-screenshot-2026-06-04-at-11-40-55-am.png)

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

![Answer SELECT_CHALLENGE with PASSWORD](/assets/temp/081-screenshot-2026-06-04-at-11-42-52-am.png)

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

![Respond to SOFTWARE_TOKEN_MFA](/assets/temp/086-screenshot-2026-06-04-at-11-43-37-am.png)

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

![Export returned tokens](/assets/temp/108-screenshot-2026-06-04-at-11-44-11-am.png)

Authentication result:

![MFA response with AuthenticationResult](/assets/temp/022-screenshot-2026-06-04-at-12-17-40-pm.png)

> [!IMPORTANT]
> Use `$ACCESS_TOKEN` for the scoped API Gateway method tests. The ID token is still useful for inspecting identity claims, but it is not the token to send when method authorization scopes are configured.

## 16. Token Helper Script Authentication With The No-Secret Client

This section uses the default no-secret app client named `chewbacca-auth-rest-users`.

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

![Create public helper client](/assets/temp/047-screenshot-2026-06-04-at-11-46-54-am.png)

Install dependencies for token helper scripts:

```bash
cd "$REPO_ROOT"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r shared/scripts/requirements.txt
```

Token helper script dependency install:

![Install helper script dependencies](/assets/temp/069-screenshot-2026-06-04-at-11-47-12-am.png)

Run the `easier_get_token.py` script:

```bash
python shared/scripts/easier_get_token.py
```

`easier_get_token.py` run output:

![Export helper script values and run easier_get_token](/assets/temp/102-screenshot-2026-06-04-at-11-57-50-am.png)

`easier_get_token.py` token response:

![Easier token helper output](/assets/temp/113-screenshot-2026-06-04-at-12-08-49-pm.png)

`easier_get_token.py` token output:

![Easier token helper token output](/assets/temp/008-screenshot-2026-06-04-at-12-10-54-pm.png)

Run the `flavor_get_token.py` script:

```bash
python shared/scripts/flavor_get_token.py
```

`flavor_get_token.py` script output:

![Run flavor_get_token](/assets/temp/035-screenshot-2026-06-04-at-11-59-07-am.png)

The `flavor_get_token.py` script should decode token claims and print curl examples for:

```text
${API_BASE}/jedi
${API_BASE}/sith
```

Curl examples from `flavor_get_token.py`:

![Helper-generated curl examples](/assets/temp/003-screenshot-2026-06-04-at-11-59-33-am.png)

Access token claims:

![Access token claims](/assets/temp/055-screenshot-2026-06-04-at-11-59-44-am.png)

Token helper script API test with access token:

![Helper API test with access token](/assets/temp/012-screenshot-2026-06-04-at-12-00-02-pm.png)

> [!NOTE]
> These token helper scripts are convenience tools after the learning pass. If the selected app client has a secret, the script flow will fail because these scripts do not send `SECRET_HASH`.

## 17. Test Protected REST API Routes With Access Tokens

Because the REST methods require `aws.cognito.signin.user.admin`, use `$ACCESS_TOKEN`.

Manual form:

```bash
curl -i \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "<API_ENDPOINT>/prod/jedi?name=Chewbacca"
```

Export form:

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"

curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected:

```text
HTTP/2 200
```

Protected route tests:

![Protected Jedi and Sith routes with access token](/assets/temp/054-screenshot-2026-06-04-at-12-01-57-pm.png)

Protected Jedi route returns HTTP 200:

![Protected Jedi route returns HTTP 200](/assets/temp/009-screenshot-2026-06-04-at-12-08-19-pm.png)

Validation:

- Public route test before authorizer returns `200`.
- Missing token after authorizer returns `401`.
- Access token after successful MFA returns `200`.
- Lambda logs appear only when authorization succeeds.

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

![Direct flow shortcut to SOFTWARE_TOKEN_MFA](/assets/temp/066-screenshot-2026-06-04-at-12-17-25-pm.png)

This shortcut is useful after the manual learning pass, but it does not teach the `SELECT_CHALLENGE` negotiation step.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unable to verify secret hash` | Wrong username, client ID, client secret, or copied hash | Regenerate `SECRET_HASH` using the exact username, client ID, and client secret |
| `InvalidParameterException` for `USER_AUTH` | App client does not allow `ALLOW_USER_AUTH` | Edit the app client and enable choice-based sign-in |
| `Invalid session` | Session reused from the wrong flow, user, app client, or expired challenge chain | Restart from `USER_AUTH` and use each new session in order |
| `CodeMismatchException` | Expired or incorrect TOTP code | Wait for a newly generated code and retry |
| MFA not challenged after password | User has not enrolled TOTP or MFA preference is not set | Complete MFA enrollment again |
| `{"message":"Unauthorized"}` with token | Wrong token type, expired token, missing scope, bad header, or stale deployment | Use `$ACCESS_TOKEN`, confirm `aws.cognito.signin.user.admin` scope, and redeploy |
| Route still public | Method authorization changed but API was not redeployed | Deploy the API to `prod` again |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid requests before Lambda runs |

## Final Check

You have completed this REST lab when you can explain this flow without looking:

```text
Separate Lambda roles isolate Python and Node execution
REST resources are created before methods
Public route tests prove Lambda proxy routing before Cognito
The user pool owns the identity source
The default no-secret app client supports managed login and token helper scripts
The secret-bearing CLI app client teaches SECRET_HASH
USER_AUTH starts challenge negotiation
SELECT_CHALLENGE lets the client choose PASSWORD
PASSWORD validates the primary factor
SOFTWARE_TOKEN_MFA validates the second factor
Cognito issues JWT tokens
REST API Cognito authorizer validates the access token
Authorization scopes require ACCESS_TOKEN rather than ID_TOKEN
Lambda only runs after authorization succeeds
CloudWatch proves what actually happened
```

## References

* [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
* [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
* [API Gateway REST API Cognito authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
* [REST API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)

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
| `aws apigateway create-rest-api` | [apigateway create-rest-api](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-rest-api.html) |
| `aws apigateway get-resources` | [apigateway get-resources](https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-resources.html) |
| `aws apigateway create-resource` | [apigateway create-resource](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-resource.html) |
| `aws apigateway put-method` | [apigateway put-method](https://docs.aws.amazon.com/cli/latest/reference/apigateway/put-method.html) |
| `aws apigateway put-integration` | [apigateway put-integration](https://docs.aws.amazon.com/cli/latest/reference/apigateway/put-integration.html) |
| `aws apigateway create-deployment` | [apigateway create-deployment](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-deployment.html) |
| `aws apigateway create-authorizer` | [apigateway create-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-authorizer.html) |
| `aws apigateway update-method` | [apigateway update-method](https://docs.aws.amazon.com/cli/latest/reference/apigateway/update-method.html) |
| `aws apigateway get-authorizer` | [apigateway get-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-authorizer.html) |
| `aws cognito-idp create-user-pool` | [cognito-idp create-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/create-user-pool.html) |
| `aws cognito-idp set-user-pool-mfa-config` | [cognito-idp set-user-pool-mfa-config](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-pool-mfa-config.html) |
| `aws cognito-idp create-user-pool-client` | [cognito-idp create-user-pool-client](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/create-user-pool-client.html) |
| `aws cognito-idp describe-user-pool-client` | [cognito-idp describe-user-pool-client](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/describe-user-pool-client.html) |
| `aws cognito-idp list-user-pool-clients` | [cognito-idp list-user-pool-clients](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/list-user-pool-clients.html) |
| `aws cognito-idp admin-create-user` | [cognito-idp admin-create-user](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-create-user.html) |
| `aws cognito-idp admin-set-user-password` | [cognito-idp admin-set-user-password](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-set-user-password.html) |
| `aws cognito-idp admin-get-user` | [cognito-idp admin-get-user](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-get-user.html) |
| `aws cognito-idp initiate-auth` | [cognito-idp initiate-auth](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html) |
| `aws cognito-idp associate-software-token` | [cognito-idp associate-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/associate-software-token.html) |
| `aws cognito-idp verify-software-token` | [cognito-idp verify-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/verify-software-token.html) |
| `aws cognito-idp set-user-mfa-preference` | [cognito-idp set-user-mfa-preference](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-mfa-preference.html) |
| `aws cognito-idp respond-to-auth-challenge` | [cognito-idp respond-to-auth-challenge](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html) |

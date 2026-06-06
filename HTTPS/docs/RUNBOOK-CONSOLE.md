# Cognito Auth Flow - HTTPS Runbook - Console

Use this runbook to build the HTTPS/HTTP API Cognito auth flow through the AWS console. Keep the CLI commands for exported IDs, validation, token handling, and route testing.

This flow uses:

- Chewbacca test user
- Cognito User Pool
- public app client for Cognito managed login and token helper scripts
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
cp "$REPO_ROOT/HTTPS/env.example" \
  "$REPO_ROOT/HTTPS/.env"
```

Set the environment file path:

```bash
export ENV_FILE="$REPO_ROOT/HTTPS/.env"
```

Get the AWS account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

Open `.env` in VS Code or your editor of choice:

```bash
code "$ENV_FILE"
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
source "$ENV_FILE"
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

This build uses separate Lambda execution roles for the Python Jedi function and the Node Sith function.

### Steps

Create the Python Lambda role first.

1. Open **IAM**.
2. Click **Roles**.
3. Click **Create role**.
4. Choose trusted entity type **AWS service**.
5. Choose use case **Lambda**.
6. Click **Next**.

7. Search for `AWSLambdaBasicExecutionRole`.
8. Select the `AWSLambdaBasicExecutionRole` policy.
9. Click **Next**.

# TODO: Updated Screenshot
![Lambda execution role policy selection](/assets/images/005-lambda-role-policy-selection.png)

10. Set the role name to `chewbacca-auth-http-lambda-python-role`.

# TODO: Updated Screenshot
![Lambda execution role name](/assets/images/082-lambda-execution-role-name.png)

11. Review the permissions summary.

# TODO: Updated Screenshot
![Lambda role permission policy summary](/assets/images/037-lambda-role-policy-summary.png)

12. Click **Create role**.
13. Repeat the same steps for the Node role and name it `chewbacca-auth-http-lambda-node-role`.
14. Give IAM a few seconds to propagate before creating Lambda functions.

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

Create both Lambda functions in the console first, then use the CLI reference if you want to build the same resources from exported values.

### 4.1 Jedi Python Lambda

#### Steps

| Setting | Value |
| --- | --- |
| Function name | `chewbacca-auth-http-jedi-python` |
| Runtime | Python 3.12 |
| Execution role | `chewbacca-auth-http-lambda-python-role` |
| Handler | `lambda_function.lambda_handler` |
| ZIP file | `shared/lambda-code/jedi-python.zip` |

1. Open **Lambda**.
2. Click **Create function**.
3. Select **Author from scratch**.
4. Set **Function name** to `chewbacca-auth-http-jedi-python`.
5. Set **Runtime** to **Python 3.12**.
6. Under permissions, choose **Use an existing role**.
7. Select `chewbacca-auth-http-lambda-python-role`.
8. Click **Create function**.

# TODO: Updated Screenshot
![Create Jedi Python Lambda](/assets/images/084-create-jedi-python-lambda.png)

9. On the function page, open the **Code** tab.
10. Click **Upload from**.
11. Select **.zip file**.

# TODO: Updated Screenshot
![Select Lambda ZIP file](/assets/images/085-select-lambda-zip.png)

12. Select `shared/lambda-code/jedi-python.zip`.
13. Click **Save**.

# TODO: Updated Screenshot
![Update Lambda from ZIP file](/assets/images/046-update-lambda-zip.png)

14. Confirm Lambda reports a successful code update.

If the editor still has the old default `lambda_function.py` tab open, Lambda may show a success message and a file-not-found editor error at the same time.

# TODO: Updated Screenshot
![Upload success with stale editor tab error](/assets/images/060-upload-success-stale-tab-error.png)

15. Close the stale editor tab.
16. Open the uploaded `lambda_function.py`.

# TODO: Updated Screenshot
![Upload success after closing stale tab](/assets/images/019-upload-success-tab-closed.png)

17. If the stale tab is still visible, click the new file or close the old tab to clear the editor error.

# TODO: Updated Screenshot
![Clear the old Lambda editor tab](/assets/images/035-clear-stale-lambda-tab.png)

18. If you uploaded `jedi_python.py` directly instead of the prepared ZIP, right-click `jedi_python.py`.

# TODO: Updated Screenshot
![Right-click Lambda source file](/assets/images/077-right-click-lambda-file.png)

19. Rename it to `lambda_function.py`.
20. Confirm the handler remains `lambda_function.lambda_handler`.

# TODO: Updated Screenshot
![Rename Python Lambda file](/assets/images/007-rename-python-lambda-file.png)

### 4.2 Sith Node Lambda

#### Steps

| Setting | Value |
| --- | --- |
| Function name | `chewbacca-auth-http-sith-node` |
| Runtime | Node.js 20.x |
| Execution role | `chewbacca-auth-http-lambda-node-role` |
| Handler | `index.handler` |
| ZIP file | `shared/lambda-code/sith-node.zip` |

1. Return to **Lambda**.
2. Click **Create function**.
3. Select **Author from scratch**.
4. Set **Function name** to `chewbacca-auth-http-sith-node`.
5. Set **Runtime** to **Node.js 20.x**.
6. Under permissions, choose **Use an existing role**.
7. Select `chewbacca-auth-http-lambda-node-role`.
8. Click **Create function**.

# TODO: Updated Screenshot
![Create Sith Node Lambda](/assets/images/036-create-sith-node-lambda.png)

9. Open the **Code** tab.
10. Click **Upload from**.
11. Select **.zip file**.
12. Select `shared/lambda-code/sith-node.zip`.
13. Click **Save**.
14. If you uploaded `sith_node.js` directly instead of the prepared ZIP, rename it to `index.js`.
15. Confirm the handler remains `index.handler`.

# TODO: Updated Screenshot
![Rename Node Lambda file](/assets/images/028-rename-node-lambda-file.png)

> [!WARNING]
> Lambda handler names must match both the file name and exported function name. Python uses `lambda_function.lambda_handler`. Node uses `index.handler`. A mismatched handler causes runtime import errors even when the uploaded code is correct.

### 4.3 Confirm Lambda Permissions And Export ARNs

#### Steps

If the console created an automatic execution role, switch each function to the matching role from this runbook.

1. Open the Lambda function.
2. Click **Configuration**.
3. Click **Permissions**.

# TODO: Updated Screenshot
![Lambda permissions configuration](/assets/images/034-lambda-permissions-config.png)

4. Click **Edit** in the execution role section.

# TODO: Updated Screenshot
![Edit Lambda execution role](/assets/images/073-edit-lambda-role.png)

5. Select the matching role.

| Function | Execution role |
| --- | --- |
| Jedi Python | `chewbacca-auth-http-lambda-python-role` |
| Sith Node | `chewbacca-auth-http-lambda-node-role` |

# TODO: Updated Screenshot
![Select execution role](/assets/images/058-select-execution-role.png)

6. Click **Save**.

# TODO: Updated Screenshot
![Role update successful](/assets/images/091-lambda-role-updated.png)

7. Choose **Deploy** after code or configuration changes.
8. Repeat for the Sith Node function.

After creating the functions, export the function ARNs. This is part of the clickops workflow too: copy the function ARNs from the Lambda overview page, or use the CLI commands below.

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

Jedi Python direct test:

# TODO: Updated Screenshot
![Jedi Python direct Lambda test](/assets/images/056-jedi-python-lambda-test.png)

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

Console navigation: **API Gateway** -> **Create API** -> **HTTP API** -> API name from `API_NAME`.

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
![Unprotected API route tests](/assets/images/015-unprotected-api-tests.png)

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show API Gateway event payloads.
- The event shape is different from the direct Lambda test payload.

## 9. Create The Cognito User Pool

### Steps

1. Open **Amazon Cognito**.
2. Click **User pools**.
3. Click **Create user pool**.

# TODO: Updated Screenshot
![Select create user pool](/assets/images/078-select-create-user-pool.png)

4. For **Application type**, select **Single page application**.

# TODO: Updated Screenshot
![User pool application type](/assets/images/074-user-pool-application-type.png)

5. Set **User pool name** to `chewbacca-auth-http-users`.
6. Under sign-in identifiers, select **Email** and **Username**.
7. Under required sign-up attributes, select **Birthdate**, **Email**, **Name**, and **Phone number**.
8. Continue through the remaining configuration screens.

# TODO: Updated Screenshot
![User pool configuration](/assets/images/068-user-pool-configuration.png)

9. Click **Create user pool**.

# TODO: Updated Screenshot
![Create user pool success](/assets/images/059-user-pool-created.png)

10. If Cognito generated a default name, open the user pool **Overview** page.
11. Click **Rename**.

# TODO: Updated Screenshot
![Select rename user pool](/assets/images/013-select-rename-user-pool.png)

12. Replace the default name with `chewbacca-auth-http-users`.

# TODO: Updated Screenshot
![Rename user pool](/assets/images/017-rename-user-pool.png)

13. Save the rename.

# TODO: Updated Screenshot
![User pool rename success](/assets/images/031-user-pool-renamed.png)

14. On the user pool overview page, copy the user pool ID.

# TODO: Updated Screenshot
![User pool ID](/assets/images/090-user-pool-id.png)

15. Export the user pool ID for the remaining commands:

```bash
export USER_POOL_ID="<USER_POOL_ID_FROM_CONSOLE>"
```

16. Export the issuer and user pool ARN:

```bash
export COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"
export USER_POOL_ARN="arn:aws:cognito-idp:${AWS_REGION}:${AWS_ACCOUNT_ID}:userpool/${USER_POOL_ID}"

echo "$USER_POOL_ID"
echo "$COGNITO_ISSUER"
echo "$USER_POOL_ARN"
```

# TODO: Updated Screenshot
![User pool export validation](/assets/images/102-user-pool-export-validation.png)

## 10. Enable Software Token MFA

### Steps

1. Open the user pool.
2. Click **Authentication**.
3. Click **Sign-in**.
4. In the **Multi-factor authentication** tile, click **Edit**.

# TODO: Updated Screenshot
![Select edit MFA](/assets/images/066-select-edit-mfa.png)

5. Under **MFA authentication**, choose **Require MFA - Recommended**.
6. Under MFA methods, select **Authenticator apps**.
7. Click **Save**.

# TODO: Updated Screenshot
![Edit MFA settings](/assets/images/020-edit-mfa-settings.png)

## 11. Configure App Clients

This runbook uses one required no-secret app client and supports one optional secret-bearing app client:

| Client | Secret | Purpose |
| --- | --- | --- |
| Default `chewbacca-auth-http-users` client | No secret | Managed login and token helper scripts |
| Optional `chewbacca-auth-http-cli-client` client | Secret | `SECRET_HASH` validation flow |

### 11.1 Edit The Default No-Secret App Client

#### Steps

1. In the user pool, click **Applications**.
2. Click **App clients**.
3. Click the default `chewbacca-auth-http-users` app client.
4. In the **App client information** tile, click **Edit**.

# TODO: Updated Screenshot
![Select edit default app client information](/assets/images/051-select-edit-default-client.png)

5. Enable these authentication flows:

- Choice-based sign-in: `ALLOW_USER_AUTH`
- Sign in with username and password: `ALLOW_USER_PASSWORD_AUTH`
- Sign in with secure remote password: `ALLOW_USER_SRP_AUTH`
- Get new user tokens from existing authenticated sessions: `ALLOW_REFRESH_TOKEN_AUTH`

6. Set these token values:

| Token setting | Value |
| --- | --- |
| Authentication flow session duration | 15 minutes |
| Access token expiration | 60 minutes |
| ID token expiration | 60 minutes |
| Refresh token expiration | 1 day |

# TODO: Updated Screenshot
![Default app client auth flow settings](/assets/images/040-default-client-auth-flow.png)

7. Click **Save changes**.

# TODO: Updated Screenshot
![Edit default app client success](/assets/images/101-default-client-edited.png)

8. Copy the default no-secret app client ID and export it:

```bash
export COGNITO_PUBLIC_CLIENT_ID="<DEFAULT_NO_SECRET_CLIENT_ID>"
```

### 11.2 Create The Additional Secret-Bearing CLI App Client

> [!IMPORTANT]
> This step is optional: Only create a secret-bearing app client if you need to validate `SECRET_HASH` flows.

Create this app client only when you need to validate `SECRET_HASH` flows.

#### Steps

1. In the user pool, click **Applications**.
2. Click **App clients**.
3. Click **Create app client**.

# TODO: Updated Screenshot
![Select create app client](/assets/images/029-select-create-app-client.png)

4. In **Define your application**, set these values:

| Setting | Value |
| --- | --- |
| Application type | Traditional web application |
| App client name | `chewbacca-auth-http-cli-client` |
| Client secret | Generate client secret |
| Authentication flow session duration | 15 minutes |
| Access token expiration | 60 minutes |
| ID token expiration | 60 minutes |
| Refresh token expiration | 1 day |

# TODO: Updated Screenshot
![CLI app client configuration](/assets/images/030-cli-client-configuration.png)

5. Click **Create app client**.

# TODO: Updated Screenshot
![CLI app client created successfully](/assets/images/002-cli-client-created.png)

6. Open the new `chewbacca-auth-http-cli-client` app client.
7. In the **App client information** tile, click **Edit**.

# TODO: Updated Screenshot
![Select edit CLI app client information](/assets/images/048-select-edit-cli-client.png)

8. Enable these authentication flows:

- Choice-based sign-in: `ALLOW_USER_AUTH`
- Sign in with username and password: `ALLOW_USER_PASSWORD_AUTH`
- Sign in with secure remote password: `ALLOW_USER_SRP_AUTH`
- Get new user tokens from existing authenticated sessions: `ALLOW_REFRESH_TOKEN_AUTH`

# TODO: Updated Screenshot
![CLI app client auth flow settings](/assets/images/026-cli-client-auth-flow.png)

9. Confirm the token duration values remain:

| Token setting | Value |
| --- | --- |
| Authentication flow session duration | 15 minutes |
| Access token expiration | 60 minutes |
| ID token expiration | 60 minutes |
| Refresh token expiration | 1 day |

10. Click **Save changes**.

# TODO: Updated Screenshot
![Edit CLI app client success](/assets/images/108-cli-client-edited.png)

11. On the app client page, copy the client ID.

# TODO: Updated Screenshot
![Get CLI app client ID](/assets/images/004-get-cli-client-id.png)

12. Export it:

```bash
export CLIENT_ID="<CLI_SECRET_CLIENT_ID>"
```

13. Click **Show client secret**.
14. Copy the client secret and export it:

```bash
export CLIENT_SECRET="<CLI_CLIENT_SECRET>"
```

15. Describe the app client and validate the exported values:

```bash
export CLIENT_JSON=$(aws cognito-idp describe-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --query 'UserPoolClient' \
  --output json \
  --region "$AWS_REGION")

echo "$CLIENT_ID"
echo "${CLIENT_SECRET:0:8}..."
echo "$CLIENT_JSON" | jq '{ClientName,ExplicitAuthFlows,AuthSessionValidity,AccessTokenValidity,IdTokenValidity,RefreshTokenValidity,TokenValidityUnits}'
```

# TODO: Updated Screenshot
![Export and validate CLI app client JSON](/assets/images/052-validate-cli-client-json.png)

> [!IMPORTANT]
> Do not commit real secrets. The export command stores the full client secret, but the validation command in this runbook only prints a short prefix for validation.

### 11.3 Create Managed Login Styling

#### Steps

1. In the user pool, click **Branding**.
2. Click **Managed login**.
3. Click **Create style** in the styles tile.

> [!NOTE]
> Cognito managed login can show a browser error if a login page style has not been created and assigned. Create the style before using **View login page**.

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

Create the user in Cognito, then complete the hosted login flow for continuity.

### 12.1 Admin Create The User

#### Steps

1. Open the user pool.
2. Click **Users**.
3. Click **Create user**.

# TODO: Updated Screenshot
![Select create user](/assets/images/044-select-create-user.png)

4. Enter these values:

| Setting | Value |
| --- | --- |
| Username | `chewbacca` |
| Email | `$TEST_EMAIL` |
| Invitation | Do not send invitation |
| Temporary password | `Wookiee#TEMP1!` |

# TODO: Updated Screenshot
![User information](/assets/images/070-user-information.png)

5. Click **Create user**.

# TODO: Updated Screenshot
![User created successfully in console](/assets/images/089-user-created-console.png)

### 12.2 Managed Login Completion Path

Use this option when you want the user to experience the hosted Cognito login flow:

#### Steps

1. Open **View login page** from the app client.

# TODO: Updated Screenshot
![View CLI app client login page](/assets/images/071-view-app-client-login-page.png)

2. Sign in with username `chewbacca`.
3. Enter temporary password `Wookiee#TEMP1!`.

# TODO: Updated Screenshot
![CLI app sign-in](/assets/images/011-app-client-sign-in.png)

# TODO: Updated Screenshot
![CLI app sign-in screen](/assets/images/088-app-client-sign-in-screen.png)

4. Change password to `Wookiee#2026!`.
5. Enter full name `Chewbacca Raaawr`.
6. Enter a real phone number if prompted.

# TODO: Updated Screenshot
![CLI app change password](/assets/images/047-app-client-change-password.png)

If the challenge takes too long, Cognito may show a session expiration warning:

# TODO: Updated Screenshot
![Session expired warning](/assets/images/100-session-expired-warning.png)

7. Set up authenticator app MFA.

# TODO: Updated Screenshot
![Set up authenticator app](/assets/images/024-set-up-authenticator-app.png)

8. Scan the QR code or click **Show secret key** and add the key manually to your authenticator app.

# TODO: Updated Screenshot
![Desktop authenticator setup](/assets/images/105-authenticator-secret-setup.png)

9. Enter the current authenticator code.

# TODO: Updated Screenshot
![Desktop authenticator code generated](/assets/images/092-authenticator-code-generated.png)

10. Click **Sign in**.

# TODO: Updated Screenshot
![Successful sign-in](/assets/images/032-successful-sign-in.png)

> [!NOTE]
> If the challenge session expires during managed login, restart the hosted login sequence. This runbook uses a 15-minute authentication flow session duration; access and ID tokens remain valid for 60 minutes.

Alternate temporary-password challenge flow:

# TODO: Updated Screenshot
![Respond to new password challenge](/assets/images/014-new-password-challenge.png)

## 13. Add The HTTP API JWT Authorizer

Create the HTTP API JWT authorizer:

Console navigation: open the HTTP API -> **Authorization** -> **Manage authorizers** -> **Create**. Use a JWT authorizer with issuer `COGNITO_ISSUER`, audience `CLIENT_ID`, and identity source `$request.header.Authorization`. Attach it to `GET /jedi` and `GET /sith`.

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

## 15. Token Helper Script Authentication With The No-Secret Client

Use the default no-secret app client named `chewbacca-auth-http-users`.

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
> If the selected app client has a secret, the token helper script flow will fail because these scripts do not send `SECRET_HASH`.

## 16. Test Protected HTTP API Routes With Access Tokens

Copy the access token from `easier_get_token.py` or `flavor_get_token.py`, then export it for route testing:

```bash
export ACCESS_TOKEN="<ACCESS_TOKEN_FROM_TOKEN_HELPER_SCRIPT>"
```

Test the Jedi route:

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Expected:

```text
HTTP/2 200
...
```

> [!NOTE]
> If the response says `The incoming token has expired`, do not chase the Lambda first. API Gateway rejected the request before invocation. Run the token helper script again and retry with a newly generated access token.

Test the Sith route:

This confirms the authorizer is attached to both protected routes.

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/sith?name=Chewbacca"
```

Expected:

```text
HTTP/2 200
...
```

Protected route tests:

# TODO: Updated Screenshot
![Protected Jedi and Sith routes with access token](/assets/images/049-protected-routes-access-token.png)

Protected Jedi route returns HTTP 200:

# TODO: Updated Screenshot
![Protected Jedi route returns HTTP 200](/assets/images/009-protected-jedi-200-response.png)

Validation:

- Public pre-authorizer test returns `200`.
- Missing token after authorizer attachment returns `401`.
- Valid token returns `200`.
- Lambda logs appear only when authorization succeeds.

## 17. Optional SECRET_HASH Validation

Use this section only when you need to validate the optional secret-bearing app client and `SECRET_HASH` flow.

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

### 17.1 Enroll TOTP With A Temporary Access Token

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

Copy `SecretCode` into your authenticator app as a manual secret.

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
> The two software-token screenshots above show the challenge-session enrollment variant. The primary command flow in this runbook uses `TEMP_ACCESS_TOKEN`; both approaches are valid Cognito enrollment patterns when the session or access token belongs to the same active authentication flow.

### 17.2 Alternate Option: Enroll TOTP Through Managed Login

Use this option when you want to enroll MFA through the hosted Cognito login page instead of the CLI software-token commands.

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

After this flow, continue with `USER_AUTH`. You do not need to repeat the CLI software-token enrollment commands unless you want to practice both methods.

### 17.3 Start `USER_AUTH`

Start `USER_AUTH` and save the returned `Session` value.

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

### 17.4 Answer `SELECT_CHALLENGE` With `PASSWORD`

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

### 17.5 Respond To `SOFTWARE_TOKEN_MFA`

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

## 18. Optional Direct Flow Shortcut

Use this optional shortcut after validating the secret-bearing app client. `USER_PASSWORD_AUTH` skips `SELECT_CHALLENGE` and goes directly to password validation, then MFA.

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

This shortcut bypasses the `SELECT_CHALLENGE` negotiation step.

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

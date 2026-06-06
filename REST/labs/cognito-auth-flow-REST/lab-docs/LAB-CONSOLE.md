# Cognito Auth Flow - REST Lab - Console

This lab teaches the REST implementation of the Cognito auth flow. You will practice the AWS console path, use a local `.env` file for planned values, resource outputs, and CLI validation, and keep the conceptual checkpoints that explain how Cognito, API Gateway, Lambda, and MFA fit together.

This flow uses:

- Chewbacca test user
- Cognito User Pool
- Default public app client for token helper scripts
- Additional secret-bearing CLI app client for `SECRET_HASH`
- `USER_AUTH` and `SELECT_CHALLENGE`
- `PASSWORD`
- `SOFTWARE_TOKEN_MFA`
- Access token with `aws.cognito.signin.user.admin` scope
- API Gateway REST API Cognito authorizer
- Protected `/prod/jedi` and `/prod/sith` Lambda routes

> [!IMPORTANT]
> REST methods are protected with an authorization scope. Once `aws.cognito.signin.user.admin` is configured on the API methods, use the Cognito **access token** for protected route tests. Do not use the ID token for the scoped route test.

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

Set the repo root so you can copy the template into the lab folder:

```bash
export REPO_ROOT="<COGNITO_CLI_AUTH_FLOW_REPO_ROOT>"
cd "$REPO_ROOT"
```

Example:

```bash
export REPO_ROOT="/Users/kirk/devsecops/cognito-cli-auth-flow"
cd "$REPO_ROOT"
```

## 1. Create And Load The Lab Environment File

An environment file helps simplify deployment and provides a record of planned values and resource outputs. You will copy the dotenv template, rename the copy to `.env`, update initial values, then reload it before running commands that depend on those values.

Copy the template:

```bash
cp "$REPO_ROOT/REST/labs/cognito-auth-flow-REST/env.example" \
  "$REPO_ROOT/REST/labs/cognito-auth-flow-REST/.env"
```

Set the environment file path:

```bash
export LAB_ENV="$REPO_ROOT/REST/labs/cognito-auth-flow-REST/.env"
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
PROJECT_NAME="chewbacca-auth-rest"
TEST_USERNAME="chewbacca"
TEST_EMAIL="chewbacca@example.com"
TEST_PASSWORD="Wookiee#2026!"
TEMP_PASSWORD="Wookiee#TEMP1!"
```

Save `.env`, then load it once for the first build phase:

```bash
set -a
source "$LAB_ENV"
set +a
```

> [!IMPORTANT]
> `TEST_EMAIL` must be an active email account you can access for identity verification and managed-login testing. `TEST_USERNAME`, `TEST_PASSWORD`, and `TEMP_PASSWORD` can be customized, but keep the values consistent throughout the lab.

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
> Stop here if any value is wrong. Later commands reuse these environment values for ARNs, Lambda permissions, Cognito clients, and REST method authorization.

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

![Lambda execution role policy selection](/assets/images/005-lambda-role-policy-selection.png)

10. Set the role name to `chewbacca-auth-rest-lambda-python-role`.

![Lambda execution role name](/assets/images/082-lambda-execution-role-name.png)

11. Review the permissions summary.

![Lambda role permission policy summary](/assets/images/037-lambda-role-policy-summary.png)

12. Click **Create role**.
13. Repeat the same steps for the Node role and name it `chewbacca-auth-rest-lambda-node-role`.
14. Give IAM a few seconds to propagate before creating Lambda functions.

Record both role ARNs in `.env` as one group. You can copy each ARN from the IAM role summary page, or retrieve them with the CLI:

```bash
aws iam get-role \
  --role-name "$PYTHON_LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text

aws iam get-role \
  --role-name "$NODE_LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text
```

Add both returned values to `.env` and save the file:

```bash
PYTHON_LAMBDA_ROLE_ARN="<PYTHON_LAMBDA_ROLE_ARN>"
NODE_LAMBDA_ROLE_ARN="<NODE_LAMBDA_ROLE_ARN>"
```

Reload `.env` before packaging and creating Lambda functions:

```bash
set -a
source "$LAB_ENV"
set +a

printf '%s\n' "$PYTHON_LAMBDA_ROLE_ARN" "$NODE_LAMBDA_ROLE_ARN"
```

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

![Package Lambda ZIP files](/assets/images/095-package-lambda-zips.png)

## 4. Create The Lambda Functions

Create both Lambda functions in the console first, then use the CLI reference if you want to build the same resources from exported values.

### 4.1 Jedi Python Lambda

#### Steps

| Setting | Value |
| --- | --- |
| Function name | `chewbacca-auth-rest-jedi-python` |
| Runtime | Python 3.12 |
| Execution role | `chewbacca-auth-rest-lambda-python-role` |
| Handler | `lambda_function.lambda_handler` |
| ZIP file | `shared/lambda-code/jedi-python.zip` |

1. Open **Lambda**.
2. Click **Create function**.
3. Select **Author from scratch**.
4. Set **Function name** to `chewbacca-auth-rest-jedi-python`.
5. Set **Runtime** to **Python 3.12**.
6. Under permissions, choose **Use an existing role**.
7. Select `chewbacca-auth-rest-lambda-python-role`.
8. Click **Create function**.

![Create Jedi Python Lambda](/assets/images/084-create-jedi-python-lambda.png)

9. On the function page, open the **Code** tab.
10. Click **Upload from**.
11. Select **.zip file**.

![Select Lambda ZIP file](/assets/images/085-select-lambda-zip.png)

12. Select `shared/lambda-code/jedi-python.zip`.
13. Click **Save**.

![Update Lambda from ZIP file](/assets/images/046-update-lambda-zip.png)

14. Confirm Lambda reports a successful code update.

If the editor still has the old default `lambda_function.py` tab open, Lambda may show a success message and a file-not-found editor error at the same time.

![Upload success with stale editor tab error](/assets/images/060-upload-success-stale-tab-error.png)

15. Close the stale editor tab.
16. Open the uploaded `lambda_function.py`.

![Upload success after closing stale tab](/assets/images/019-upload-success-tab-closed.png)

17. If the stale tab is still visible, click the new file or close the old tab to clear the editor error.

![Clear the old Lambda editor tab](/assets/images/035-clear-stale-lambda-tab.png)

18. If you uploaded `jedi_python.py` directly instead of the prepared ZIP, right-click `jedi_python.py`.

![Right-click Lambda source file](/assets/images/077-right-click-lambda-file.png)

19. Rename it to `lambda_function.py`.
20. Confirm the handler remains `lambda_function.lambda_handler`.

![Rename Python Lambda file](/assets/images/007-rename-python-lambda-file.png)

### 4.2 Sith Node Lambda

#### Steps

| Setting | Value |
| --- | --- |
| Function name | `chewbacca-auth-rest-sith-node` |
| Runtime | Node.js 20.x |
| Execution role | `chewbacca-auth-rest-lambda-node-role` |
| Handler | `index.handler` |
| ZIP file | `shared/lambda-code/sith-node.zip` |

1. Return to **Lambda**.
2. Click **Create function**.
3. Select **Author from scratch**.
4. Set **Function name** to `chewbacca-auth-rest-sith-node`.
5. Set **Runtime** to **Node.js 20.x**.
6. Under permissions, choose **Use an existing role**.
7. Select `chewbacca-auth-rest-lambda-node-role`.
8. Click **Create function**.

![Create Sith Node Lambda](/assets/images/036-create-sith-node-lambda.png)

9. Open the **Code** tab.
10. Click **Upload from**.
11. Select **.zip file**.
12. Select `shared/lambda-code/sith-node.zip`.
13. Click **Save**.
14. If you uploaded `sith_node.js` directly instead of the prepared ZIP, rename it to `index.js`.
15. Confirm the handler remains `index.handler`.

![Rename Node Lambda file](/assets/images/028-rename-node-lambda-file.png)

> [!WARNING]
> Lambda handler names must match both the file name and exported function name. Python uses `lambda_function.lambda_handler`. Node uses `index.handler`. A mismatched handler causes runtime import errors even when the uploaded code is correct.

### 4.3 Confirm Lambda Permissions And Export ARNs

#### Steps

If the console created an automatic execution role, switch each function to the matching role from this lab.

1. Open the Lambda function.
2. Click **Configuration**.
3. Click **Permissions**.

![Lambda permissions configuration](/assets/images/034-lambda-permissions-config.png)

4. Click **Edit** in the execution role section.

![Edit Lambda execution role](/assets/images/073-edit-lambda-role.png)

5. Select the matching role.

| Function | Execution role |
| --- | --- |
| Jedi Python | `chewbacca-auth-rest-lambda-python-role` |
| Sith Node | `chewbacca-auth-rest-lambda-node-role` |

![Select execution role](/assets/images/058-select-execution-role.png)

6. Click **Save**.

![Role update successful](/assets/images/091-lambda-role-updated.png)

7. Choose **Deploy** after code or configuration changes.
8. Repeat for the Sith Node function.

After creating the functions, record the function ARNs in `.env`. This is part of the clickops workflow too: copy the function ARNs from the Lambda overview page, or use the CLI commands below.

```bash
aws lambda get-function \
  --function-name "$JEDI_FUNCTION" \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region "$AWS_REGION"

aws lambda get-function \
  --function-name "$SITH_FUNCTION" \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region "$AWS_REGION"
```

Add both returned ARNs to `.env` and save the file:

```bash
JEDI_FUNCTION_ARN="<JEDI_FUNCTION_ARN>"
SITH_FUNCTION_ARN="<SITH_FUNCTION_ARN>"
```

Reload `.env` before testing the Lambda functions:

```bash
set -a
source "$LAB_ENV"
set +a

printf '%s\n' "$JEDI_FUNCTION_ARN" "$SITH_FUNCTION_ARN"
```

Function ARN environment validation:

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

![Jedi Python direct Lambda test](/assets/images/056-jedi-python-lambda-test.png)

Jedi Python invoke success:

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

![Sith Node invoke success](/assets/images/023-sith-node-invoke-success.png)

## 6. Create The REST API And Resources

### Steps

| Setting | Value |
| --- | --- |
| API name | `chewbacca-auth-rest-api` |
| Endpoint type | Regional |

1. Open **API Gateway**.
2. Click **Create API**.
3. Find **REST API** and click **Build**.
4. Choose **New API**.
5. Set **API name** to `chewbacca-auth-rest-api`.
6. Set **Endpoint type** to **Regional**.
7. Click **Create API**.

Create the REST resources after the API exists.

| Resource | Parent path | Console location | Value |
| --- | --- | --- | --- |
| Jedi resource | `/` | API Gateway resources | `jedi` |
| Sith resource | `/` | API Gateway resources | `sith` |

8. Open the REST API **Resources** view.
9. Select the root `/` resource.
10. Click **Create resource**.

![Select create resource](/assets/images/038-select-create-resource.png)

11. Leave **Resource path** as `/`.
12. Set **Resource name** to `jedi`.
13. Click **Create resource**.

![Create Jedi resource](/assets/images/081-create-jedi-resource.png)

14. Confirm the `/jedi` resource appears.

![Jedi resource creation success](/assets/images/067-jedi-resource-created.png)

15. Select the root `/` resource again.
16. Click **Create resource**.
17. Leave **Resource path** as `/`.
18. Set **Resource name** to `sith`.
19. Click **Create resource**.

20. Copy the root `/`, `/jedi`, and `/sith` resource IDs from API Gateway.
21. Open **API settings** and copy the API ID.
22. Add the REST API values to `.env` as one group and save the file:

```bash
REST_API_ID="<REST_API_ID_FROM_CONSOLE>"
ROOT_RESOURCE_ID="<ROOT_RESOURCE_ID_FROM_CONSOLE>"
JEDI_RESOURCE_ID="<JEDI_RESOURCE_ID_FROM_CONSOLE>"
SITH_RESOURCE_ID="<SITH_RESOURCE_ID_FROM_CONSOLE>"
```

`API_ENDPOINT` is derived in `.env` from `REST_API_ID` and `AWS_REGION`.

23. Reload `.env` before creating methods and integrations:

```bash
set -a
source "$LAB_ENV"
set +a
```

24. Validate the clickops environment values:

```bash
echo "$REST_API_ID"
echo "$ROOT_RESOURCE_ID"
echo "$JEDI_RESOURCE_ID"
echo "$SITH_RESOURCE_ID"
echo "$API_ENDPOINT"
```

The output should print the values in this order:

```text
<REST_API_ID_FROM_CONSOLE>
<ROOT_RESOURCE_ID_FROM_CONSOLE>
<JEDI_RESOURCE_ID_FROM_CONSOLE>
<SITH_RESOURCE_ID_FROM_CONSOLE>
https://<REST_API_ID_FROM_CONSOLE>.execute-api.<AWS_REGION>.amazonaws.com
```

## 7. Add REST Methods And Lambda Proxy Integrations

Create public `GET` methods before adding Cognito. This proves routing works before authorization.

### Steps

1. Click the `/jedi` resource.
2. Click **Create method**.

![Select create method](/assets/images/022-select-create-method.png)

3. Method type: `GET`.
4. Integration type: Lambda function.
5. Turn on **Lambda proxy integration**.
6. Response transfer mode: `Buffered`.
7. Lambda function: select `chewbacca-auth-rest-jedi-python` or paste `$JEDI_FUNCTION_ARN`.

![Create method configuration](/assets/images/094-create-method-config.png)

8. Confirm Lambda integration is selected.

![Select Lambda integration](/assets/images/072-select-lambda-integration.png)

9. Click **Create method**.

![Method creation success](/assets/images/107-method-created.png)

10. Repeat the same method setup for `/sith`.
11. Select `chewbacca-auth-rest-sith-node` for the Sith Lambda integration.
12. Confirm both resources have `GET` methods.

![Resource and method confirmation](/assets/images/097-resource-method-confirmation.png)

13. Click **Deploy API**.

![Click deploy API](/assets/images/010-click-deploy-api.png)

14. Choose **New stage**.

![Select create stage](/assets/images/001-select-create-stage.png)

15. Set **Stage name** to `prod`.

![Add stage](/assets/images/043-add-stage.png)

16. Add deployment description `Public Jedi and Sith baseline before Cognito authorizer`.
17. Click **Deploy**.

![API deployment success](/assets/images/065-api-deployment-success.png)

18. Open **API settings**.
19. Confirm the same API ID you exported in Section 6.

![API settings API ID](/assets/images/099-api-id-settings.png)

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

Jedi route test before the authorizer:

![Test API before authorizer](/assets/images/054-test-api-before-authorizer.png)

Both unprotected route tests:

![Unprotected API path tests](/assets/images/015-unprotected-api-tests.png)

Validation:

- API Gateway reaches both Lambda functions.
- CloudWatch logs show Lambda proxy event payloads.
- If either request fails now, fix routing before adding Cognito.

## 9. Create The Cognito User Pool

### Steps

1. Open **Amazon Cognito**.
2. Click **User pools**.
3. Click **Create user pool**.

![Select create user pool](/assets/images/078-select-create-user-pool.png)

4. For **Application type**, select **Single page application**.

![User pool application type](/assets/images/074-user-pool-application-type.png)

5. Set **User pool name** to `chewbacca-auth-rest-users`.
6. Under sign-in identifiers, select **Email** and **Username**.
7. Under required sign-up attributes, select **Birthdate**, **Email**, **Name**, and **Phone number**.
8. Continue through the remaining configuration screens.

![User pool configuration](/assets/images/068-user-pool-configuration.png)

9. Click **Create user pool**.

![Create user pool success](/assets/images/059-user-pool-created.png)

10. If Cognito generated a default name, open the user pool **Overview** page.
11. Click **Rename**.

![Select rename user pool](/assets/images/013-select-rename-user-pool.png)

12. Replace the default name with `chewbacca-auth-rest-users`.

![Rename user pool](/assets/images/017-rename-user-pool.png)

13. Save the rename.

![User pool rename success](/assets/images/031-user-pool-renamed.png)

14. On the user pool overview page, copy the user pool ID.

![User pool ID](/assets/images/090-user-pool-id.png)

15. Add the user pool ID to `.env` and save the file:

```bash
USER_POOL_ID="<USER_POOL_ID_FROM_CONSOLE>"
```

`COGNITO_ISSUER` and `USER_POOL_ARN` are derived in `.env` from `AWS_REGION`, `AWS_ACCOUNT_ID`, and `USER_POOL_ID`.

16. Reload `.env` before configuring app clients, then validate the Cognito values:

```bash
set -a
source "$LAB_ENV"
set +a

echo "$USER_POOL_ID"
echo "$COGNITO_ISSUER"
echo "$USER_POOL_ARN"
```

![User pool export validation](/assets/images/102-user-pool-export-validation.png)

## 10. Enable Software Token MFA

### Steps

1. Open the user pool.
2. Click **Authentication**.
3. Click **Sign-in**.
4. In the **Multi-factor authentication** tile, click **Edit**.

![Select edit MFA](/assets/images/066-select-edit-mfa.png)

5. Under **MFA authentication**, choose **Require MFA - Recommended**.
6. Under MFA methods, select **Authenticator apps**.
7. Click **Save**.

![Edit MFA settings](/assets/images/020-edit-mfa-settings.png)

## 11. Configure App Clients

This build uses two app clients:

| Client | Secret | Purpose |
| --- | --- | --- |
| Default `chewbacca-auth-rest-users` client | No secret | Managed login and token helper scripts |
| Additional `chewbacca-auth-rest-cli-client` client | Secret | Manual CLI flow with `SECRET_HASH` |

### 11.1 Edit The Default No-Secret App Client

#### Steps

1. In the user pool, click **Applications**.
2. Click **App clients**.
3. Click the default `chewbacca-auth-rest-users` app client.
4. In the **App client information** tile, click **Edit**.

![Select edit default app client information](/assets/images/051-select-edit-default-client.png)

5. Enable these authentication flows:

- Choice-based sign-in: `ALLOW_USER_AUTH`
- Sign in with username and password: `ALLOW_USER_PASSWORD_AUTH`
- Sign in with secure remote password: `ALLOW_USER_SRP_AUTH`
- Get new user tokens from existing authenticated sessions: `ALLOW_REFRESH_TOKEN_AUTH`

6. Set these token values:

| Token setting | Value |
| --- | --- |
| Authentication flow session duration | 5 minutes |
| Access token expiration | 60 minutes |
| ID token expiration | 60 minutes |
| Refresh token expiration | 1 day |

![Default app client auth flow settings](/assets/images/040-default-client-auth-flow.png)

7. Click **Save changes**.

![Edit default app client success](/assets/images/101-default-client-edited.png)

8. Copy the default no-secret app client ID and add it to `.env`:

```bash
DEFAULT_CLIENT_ID="<DEFAULT_NO_SECRET_CLIENT_ID>"
```

`COGNITO_PUBLIC_CLIENT_ID` is derived from `DEFAULT_CLIENT_ID` in `.env`. You will reload `.env` after adding the secret-bearing app client values in the next section.

> [!NOTE]
> Lab values can lower access and ID token expiration to 15 minutes to make token expiration visible. If timed pressure is not the point of the run, use the 60-minute values above. If session expiration keeps interrupting enrollment, return here and confirm the app client duration settings.

### 11.2 Create The Additional Secret-Bearing CLI App Client

> [!IMPORTANT]
> This step is optional: Only create a secret-bearing app client if you need to validate `SECRET_HASH` flows.

Create this app client only when you need to validate `SECRET_HASH` flows.

#### Steps

1. In the user pool, click **Applications**.
2. Click **App clients**.
3. Click **Create app client**.

![Select create app client](/assets/images/029-select-create-app-client.png)

4. In **Define your application**, set these values:

| Setting | Value |
| --- | --- |
| Application type | Traditional web application |
| App client name | `chewbacca-auth-rest-cli-client` |
| Client secret | Generate client secret |
| Authentication flow session duration | 5 minutes |
| Access token expiration | 60 minutes |
| ID token expiration | 60 minutes |
| Refresh token expiration | 1 day |

![CLI app client configuration](/assets/images/030-cli-client-configuration.png)

5. Click **Create app client**.

![CLI app client created successfully](/assets/images/002-cli-client-created.png)

6. Open the new `chewbacca-auth-rest-cli-client` app client.
7. In the **App client information** tile, click **Edit**.

![Select edit CLI app client information](/assets/images/048-select-edit-cli-client.png)

8. Enable these authentication flows:

- Choice-based sign-in: `ALLOW_USER_AUTH`
- Sign in with username and password: `ALLOW_USER_PASSWORD_AUTH`
- Sign in with secure remote password: `ALLOW_USER_SRP_AUTH`
- Get new user tokens from existing authenticated sessions: `ALLOW_REFRESH_TOKEN_AUTH`

![CLI app client auth flow settings](/assets/images/026-cli-client-auth-flow.png)

9. Confirm the token duration values remain:

| Token setting | Value |
| --- | --- |
| Authentication flow session duration | 5 minutes |
| Access token expiration | 60 minutes |
| ID token expiration | 60 minutes |
| Refresh token expiration | 1 day |

10. Click **Save changes**.

![Edit CLI app client success](/assets/images/108-cli-client-edited.png)

11. On the app client page, copy the client ID.

![Get CLI app client ID](/assets/images/004-get-cli-client-id.png)

12. Add it to `.env`:

```bash
CLIENT_ID="<CLI_SECRET_CLIENT_ID>"
```

13. Click **Show client secret**.
14. Copy the client secret and add it to `.env`:

```bash
CLIENT_SECRET="<CLI_CLIENT_SECRET>"
```

Save `.env`, then reload once for both app clients:

```bash
set -a
source "$LAB_ENV"
set +a
```

15. Describe the secret-bearing app client and validate the environment values:

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

![Export and validate CLI app client JSON](/assets/images/052-validate-cli-client-json.png)

> [!IMPORTANT]
> Do not commit `.env` with real secrets. The environment file stores the full client secret, but the validation command in this lab only prints a short prefix for validation.

### 11.3 Create Managed Login Styling

#### Steps

1. In the user pool, click **Branding**.
2. Click **Managed login**.
3. Click **Create style** in the styles tile.

> [!NOTE]
> Cognito managed login can show a browser error if a login page style has not been created and assigned. Create the style before using **View login page**.

If you try to view the login page before creating a style, you may see this browser error:

![Login page error before style setup](/assets/images/039-login-page-style-error.png)

![Select create style](/assets/images/106-select-create-login-style.png)

4. Select `chewbacca-auth-rest-cli-client`.

![Select CLI app client for login style](/assets/images/062-select-login-style-app-client.png)

5. Click **Create**.

![Login style creation success](/assets/images/016-login-style-created.png)

6. Click the **Assigned app client** to return to the app client page.
7. Click **View login page**.

![Select view login page](/assets/images/086-select-view-login-page.png)

8. Confirm the CLI app client login page opens.

![CLI app client login page](/assets/images/087-app-client-login-page.png)

## 12. Create The Test User

This lab includes both admin-created user flow and managed-login completion flow.

### 12.1 Admin Create The User

#### Steps

1. Open the user pool.
2. Click **Users**.
3. Click **Create user**.

![Select create user](/assets/images/044-select-create-user.png)

4. Enter these values:

| Setting | Value |
| --- | --- |
| Username | `chewbacca` |
| Email | `$TEST_EMAIL` |
| Invitation | Do not send invitation |
| Temporary password | `Wookiee#TEMP1!` |

![User information](/assets/images/070-user-information.png)

5. Click **Create user**.

![User created successfully in console](/assets/images/089-user-created-console.png)

### 12.2 Managed Login Completion Path

Use this path when you want the user to experience the hosted Cognito login flow:

#### Steps

1. Open **View login page** from the app client.

![View CLI app client login page](/assets/images/071-view-app-client-login-page.png)

2. Sign in with username `chewbacca`.
3. Enter temporary password `Wookiee#TEMP1!`.

![CLI app sign-in](/assets/images/011-app-client-sign-in.png)

![CLI app sign-in screen](/assets/images/088-app-client-sign-in-screen.png)

4. Change password to `Wookiee#2026!`.
5. Enter full name `Chewbacca Raaawr`.
6. Enter a real phone number if prompted.

![CLI app change password](/assets/images/047-app-client-change-password.png)

If the challenge takes too long, Cognito may show a session expiration warning:

![Session expired warning](/assets/images/100-session-expired-warning.png)

7. Set up authenticator app MFA.

![Set up authenticator app](/assets/images/024-set-up-authenticator-app.png)

8. Scan the QR code or click **Show secret key** and add the key manually to your authenticator app.

![Desktop authenticator setup](/assets/images/105-authenticator-secret-setup.png)

9. Enter the current authenticator code.

![Desktop authenticator code generated](/assets/images/092-authenticator-code-generated.png)

10. Click **Sign in**.

![Successful sign-in](/assets/images/032-successful-sign-in.png)

> [!NOTE]
> It is common to see expired session warnings during early lab passes. This confirms the auth flow session duration is enforcing time pressure. The authentication challenge must be completed within the configured 5-minute session duration. If session expiration keeps blocking learning, return to **11.1** or **11.2** and use the 60-minute token validity values while keeping the 5-minute challenge session in mind.

Alternate temporary-password challenge path:

![Respond to new password challenge](/assets/images/014-new-password-challenge.png)

## 13. Add The REST API Cognito Authorizer

### Steps

1. Open `chewbacca-auth-rest-api` in API Gateway.
2. Click **Authorizers**.
3. Click **Create authorizer**.

![Select create authorizer](/assets/images/053-select-create-authorizer.png)

4. Enter these values:

| Setting | Value |
| --- | --- |
| Authorizer name | `chewbacca-auth-rest-cognito-authorizer` |
| Authorizer type | Cognito |
| Cognito user pool | `chewbacca-auth-rest-users` |
| Token source | `Authorization` |

![Authorizer details](/assets/images/057-authorizer-details.png)

5. Click **Create authorizer**.
6. After authorizer creation succeeds, note the authorizer ID for `chewbacca-auth-rest-cognito-authorizer`.

![Authorizer created with ID](/assets/images/076-authorizer-created.png)

7. Add the authorizer ID to `.env` and save the file:

```bash
COGNITO_AUTHORIZER_ID="<COGNITO_AUTHORIZER_ID_FROM_CONSOLE>"
```

Reload `.env` before attaching the authorizer to methods, then validate the value:

```bash
set -a
source "$LAB_ENV"
set +a

echo "$COGNITO_AUTHORIZER_ID"
```

![Export authorizer ID](/assets/images/025-export-authorizer-id.png)

8. Click **Resources**.
9. Select `/jedi`.
10. Select the `GET` method.
11. In the **Method request settings** tile, click **Edit**.

![Select edit method request](/assets/images/069-select-edit-method-request.png)

12. Set authorization type to the Cognito user pool authorizer.
13. Select `chewbacca-auth-rest-cognito-authorizer` from the authorizer dropdown.
14. Add authorization scope `aws.cognito.signin.user.admin`.

![Method request settings](/assets/images/041-method-request-settings.png)

15. Click **Save**.

![Method updated with authorizer](/assets/images/063-method-authorizer-updated.png)

16. Repeat steps 8-15 for `/sith` `GET`.
17. Click **Deploy API**.
18. Deploy to the existing `prod` stage.
19. Use deployment description `Protected Jedi and Sith routes with Cognito authorizer and scope`.

![Redeploy API after authorizer](/assets/images/083-redeploy-api-authorizer.png)

Validate the authorizer:

```bash
aws apigateway get-authorizer \
  --rest-api-id "$REST_API_ID" \
  --authorizer-id "$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```


> [!IMPORTANT]
> Because the methods now require `aws.cognito.signin.user.admin`, protected route tests must send an access token. ID tokens identify the user, but access tokens carry authorization scopes.

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

![Authorizer enforcement without token](/assets/images/109-authorizer-no-token-test.png)

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

![Generate secret hash manually](/assets/images/045-generate-secret-hash.png)

Secret hash terminal value confirmation:

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

![Associate software token](/assets/images/018-associate-software-token.png)

Copy `SecretCode` into your authenticator app as a manual secret.

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

![View CLI app client login page](/assets/images/071-view-app-client-login-page.png)

2. Sign in with username `chewbacca` and the temporary password.

![CLI app sign-in](/assets/images/011-app-client-sign-in.png)

![CLI app sign-in screen](/assets/images/088-app-client-sign-in-screen.png)

3. Change the temporary password to the permanent password exported earlier.

![CLI app change password](/assets/images/047-app-client-change-password.png)

If the challenge session expires while you are learning the flow, restart the hosted login sequence and continue with a newly generated authenticator code.

![Session expired warning](/assets/images/100-session-expired-warning.png)

4. Continue to authenticator app setup.

![Set up authenticator app](/assets/images/024-set-up-authenticator-app.png)

5. Scan the QR code or click **Show secret key** and add the key manually to your authenticator app.

![Desktop authenticator setup](/assets/images/105-authenticator-secret-setup.png)

6. Use a valid TOTP code from your authenticator app.

![Desktop authenticator code generated](/assets/images/092-authenticator-code-generated.png)

7. Complete sign-in.

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

![Export returned tokens](/assets/images/098-export-returned-tokens.png)

Authentication result:

![MFA response with AuthenticationResult](/assets/images/021-mfa-authentication-result.png)

> [!IMPORTANT]
> Use `$ACCESS_TOKEN` for the scoped API Gateway method tests. The ID token is still useful for inspecting identity claims, but it is not the token to send when method authorization scopes are configured.

## 16. Token Helper Script Authentication With The No-Secret Client

This section uses the default no-secret app client named `chewbacca-auth-rest-users`.

The token helper script values are derived in `.env`. Reload and validate them before running the scripts:

```bash
set -a
source "$LAB_ENV"
set +a

echo "$COGNITO_PUBLIC_CLIENT_ID"
echo "$COGNITO_USERNAME"
echo "$API_BASE"
```

If you did not already add the no-secret client ID to `.env`, look it up:

```bash
aws cognito-idp list-user-pool-clients \
  --user-pool-id "$USER_POOL_ID" \
  --query "UserPoolClients[?ClientName=='${DEFAULT_APP_CLIENT_NAME}'].ClientId | [0]" \
  --output text \
  --region "$AWS_REGION"
```

Add the returned value to `.env` as `DEFAULT_CLIENT_ID`, save the file, then reload `.env` before running the token helper scripts:

```bash
set -a
source "$LAB_ENV"
set +a
```

Public app client lookup for token helper scripts:

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

![Install helper script dependencies](/assets/images/064-install-helper-dependencies.png)

Run the `easier_get_token.py` script:

```bash
python shared/scripts/easier_get_token.py
```

`easier_get_token.py` run output:

![Export helper script values and run easier_get_token](/assets/images/093-run-easier-get-token.png)

`easier_get_token.py` token response:

![Easier token helper output](/assets/images/103-easier-token-helper-output.png)

`easier_get_token.py` token output:

![Easier token helper token output](/assets/images/008-easier-token-output.png)

Run the `flavor_get_token.py` script:

```bash
python shared/scripts/flavor_get_token.py
```

`flavor_get_token.py` script output:

![Run flavor_get_token](/assets/images/033-run-flavor-get-token.png)

The `flavor_get_token.py` script should decode token claims and print curl examples for:

```text
${API_BASE}/jedi
${API_BASE}/sith
```

Curl examples from `flavor_get_token.py`:

![Helper-generated curl examples](/assets/images/003-helper-curl-examples.png)

Access token claims:

![Access token claims](/assets/images/050-access-token-claims.png)

Token helper script API test with access token:

![Helper API test with access token](/assets/images/012-helper-access-token-api-test.png)

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

![Protected Jedi and Sith routes with access token](/assets/images/049-protected-routes-access-token.png)

Protected Jedi route returns HTTP 200:

![Protected Jedi route returns HTTP 200](/assets/images/009-protected-jedi-200-response.png)

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
| `{"message":"Unauthorized"}` with token | Wrong token type, expired token, missing scope, bad header, or stale deployment | Use `$ACCESS_TOKEN`, confirm `aws.cognito.signin.user.admin` scope, and redeploy |
| Route still public | Method authorization changed but API was not redeployed | Deploy the API to `prod` again |
| Lambda never logs during failed auth | Expected behavior | API Gateway rejects invalid requests before Lambda runs |

## Validation Checklist

Use this checklist before you consider the REST lab complete:

- [ ] Copy `env.example` to `.env`, update planned values, and reload it before dependent commands.
- [ ] Package both shared Lambda handlers from `shared/lambda-code/`.
- [ ] Create or configure separate Lambda roles for the Python and Node functions.
- [ ] Create the Jedi Python Lambda and Sith Node Lambda.
- [ ] Invoke both Lambda functions directly and confirm HTTP `200` responses.
- [ ] Create the REST API, `/jedi` resource, `/sith` resource, GET methods, and Lambda proxy integrations.
- [ ] Deploy the REST API to the `prod` stage.
- [ ] Test both public routes before adding Cognito and confirm they return HTTP `200`.
- [ ] Create the Cognito user pool, app clients, Chewbacca user, and MFA configuration.
- [ ] Create the managed login page app client without a client secret for browser login and token helper scripts.
- [ ] Optionally create the secret-bearing app client when you want to validate `SECRET_HASH` flows.
- [ ] Generate a valid `SECRET_HASH` when using the secret-bearing app client.
- [ ] Run the manual `USER_AUTH` flow and observe the `SELECT_CHALLENGE` response.
- [ ] Copy each Cognito `Session` value into the next matching challenge response.
- [ ] Complete the `PASSWORD` challenge and the `SOFTWARE_TOKEN_MFA` challenge with a valid TOTP code.
- [ ] Export the access token, ID token, and refresh token after MFA succeeds.
- [ ] Attach the REST API Cognito User Pool authorizer and required authorization scope to both methods.
- [ ] Redeploy the REST API after authorizer or method changes.
- [ ] Confirm both protected routes return HTTP `401` without an `Authorization` header.
- [ ] Confirm both protected routes return HTTP `200` with a valid access token.
- [ ] Run `easier_get_token.py` and `flavor_get_token.py` after the manual pass.
- [ ] Confirm CloudWatch logs appear only after API Gateway authorization succeeds.
- [ ] Run the lab teardown from `lab-docs/TEARDOWN_REST.md` when you are ready to remove the lab resources.

## Concept Takeaways

- Cognito owns user authentication, challenge negotiation, MFA validation, and JWT issuance.
- `SECRET_HASH` proves knowledge of an app client secret; it does not replace the user password or MFA factor.
- `USER_AUTH` makes the challenge sequence visible: `SELECT_CHALLENGE`, `PASSWORD`, then `SOFTWARE_TOKEN_MFA`.
- Cognito `Session` values are chain-specific. Reusing a session from another flow, user, or challenge can break authentication.
- REST API resources and methods must exist before they can be protected by a Cognito authorizer.
- REST API method changes require redeployment before the `prod` stage reflects the new authorization behavior.
- Scoped REST methods should be tested with the access token, not the ID token.
- API Gateway rejects unauthorized requests before Lambda runs, so missing Lambda logs can be proof that authorization blocked the request.
- CloudWatch is the final evidence source for whether API Gateway reached Lambda.

## Final Check

You are ready to leave this REST lab when you can explain the full path without looking:

```text
Chewbacca authenticates with Cognito
Cognito negotiates PASSWORD and SOFTWARE_TOKEN_MFA challenges
Cognito issues JWT tokens
API Gateway REST API validates the access token and required scope
Authorized requests reach the Jedi and Sith Lambda routes
Unauthorized requests stop at API Gateway
CloudWatch proves which requests reached Lambda
```

## References

* [Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
* [Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
* [API Gateway REST API Cognito authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
* [REST API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)

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

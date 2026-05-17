# Cognito CLI Auth Flow Class Note

The lab is intentionally simple:

```text
Chewbacca signs in from the CLI
Jedi and Sith routes sit behind API Gateway
Cognito issues the tokens
API Gateway validates the tokens
Lambda only runs after authorization succeeds
CloudWatch proves the request path
```

This is not a full fledged serverless application. It is small identity lab that explains the moving parts underneath larger serverless authentication designs.

## Links

- [[class7_advanced/00-class-7-advanced-main]]
- [[class7_advanced/api-gateway-and-lambda-integration]]
- [[class7_advanced/aws-lambda-basics]]
- [[class7_advanced/class7-lab-aws-lambda]]
- [[class7_advanced/tawny-port-serverless-infra-advanced-note]]
- [[aws/real-world-patterns-for-aws-lambda]]

## Resource Links

Keep these close while studying the CLI flow. The CLI commands make more sense when the official Cognito challenge model is nearby.

| Topic | Resource |
| --- | --- |
| Cognito authentication | [Amazon Cognito authentication](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html) |
| Authentication flow methods | [User pool authentication flow methods](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-authentication-flow-methods.html) |
| `InitiateAuth` | [Amazon Cognito InitiateAuth API](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html) |
| `RespondToAuthChallenge` | [Amazon Cognito RespondToAuthChallenge API](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_RespondToAuthChallenge.html) |
| AWS CLI `initiate-auth` | [AWS CLI initiate-auth](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html) |
| AWS CLI `respond-to-auth-challenge` | [AWS CLI respond-to-auth-challenge](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html) |
| AWS CLI `associate-software-token` | [AWS CLI associate-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/associate-software-token.html) |
| AWS CLI `verify-software-token` | [AWS CLI verify-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/verify-software-token.html) |
| AWS CLI `set-user-mfa-preference` | [AWS CLI set-user-mfa-preference](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-mfa-preference.html) |
| `SECRET_HASH` | [Computing secret hash values](https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html#cognito-user-pools-computing-secret-hash) |
| MFA | [Amazon Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html) |
| HTTP API JWT authorizers | [API Gateway HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html) |
| REST API Cognito authorizers | [Use Cognito user pools as REST API authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html) |
| Lambda proxy integration | [API Gateway Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html) |
| JWT structure | [JWT introduction](https://jwt.io/introduction) |

### AWS CLI Command References

These are the direct AWS CLI command reference pages for the commands used in the lab notes.

| Command | AWS CLI reference |
| --- | --- |
| `aws sts get-caller-identity` | [sts get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html) |
| `aws iam create-role` | [iam create-role](https://docs.aws.amazon.com/cli/latest/reference/iam/create-role.html) |
| `aws iam attach-role-policy` | [iam attach-role-policy](https://docs.aws.amazon.com/cli/latest/reference/iam/attach-role-policy.html) |
| `aws iam get-role` | [iam get-role](https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html) |
| `aws lambda create-function` | [lambda create-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/create-function.html) |
| `aws cognito-idp create-user-pool` | [cognito-idp create-user-pool](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/create-user-pool.html) |
| `aws cognito-idp set-user-pool-mfa-config` | [cognito-idp set-user-pool-mfa-config](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-pool-mfa-config.html) |
| `aws cognito-idp create-user-pool-client` | [cognito-idp create-user-pool-client](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/create-user-pool-client.html) |
| `aws cognito-idp admin-create-user` | [cognito-idp admin-create-user](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-create-user.html) |
| `aws cognito-idp admin-set-user-password` | [cognito-idp admin-set-user-password](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/admin-set-user-password.html) |
| `aws cognito-idp initiate-auth` | [cognito-idp initiate-auth](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html) |
| `aws cognito-idp associate-software-token` | [cognito-idp associate-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/associate-software-token.html) |
| `aws cognito-idp verify-software-token` | [cognito-idp verify-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/verify-software-token.html) |
| `aws cognito-idp set-user-mfa-preference` | [cognito-idp set-user-mfa-preference](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-mfa-preference.html) |
| `aws cognito-idp respond-to-auth-challenge` | [cognito-idp respond-to-auth-challenge](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html) |
| `aws apigatewayv2 create-api` | [apigatewayv2 create-api](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-api.html) |
| `aws apigatewayv2 create-authorizer` | [apigatewayv2 create-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigatewayv2/create-authorizer.html) |
| `aws apigateway create-rest-api` | [apigateway create-rest-api](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-rest-api.html) |
| `aws apigateway create-authorizer` | [apigateway create-authorizer](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-authorizer.html) |
| `aws apigateway update-method` | [apigateway update-method](https://docs.aws.amazon.com/cli/latest/reference/apigateway/update-method.html) |
| `aws apigateway create-deployment` | [apigateway create-deployment](https://docs.aws.amazon.com/cli/latest/reference/apigateway/create-deployment.html) |

## Concept Overview

This lab is mixed-mode on purpose. The infrastructure is created in the AWS Console so the AWS service relationships are visible. The authentication flow is tested in the CLI so the Cognito challenge sequence is explicit.

Console-owned setup:

```text
IAM role
Lambda functions
API Gateway API, integrations, routes/resources, stages, and authorizers
Cognito user pool
Cognito app client
Chewbacca test user
```

CLI-owned validation:

```text
SECRET_HASH
USER_AUTH
SELECT_CHALLENGE
PASSWORD
SOFTWARE_TOKEN_MFA
manual token inspection
exported token reuse
curl protected-route tests
```

Cognito CLI authentication is useful because it strips away the browser, hosted UI, cookies, and application session layer during testing. You see the raw authentication sequence:

```text
USERNAME + CLIENT_ID + CLIENT_SECRET
  -> SECRET_HASH
  -> initiate-auth USER_AUTH
  -> SELECT_CHALLENGE
  -> respond-to-auth-challenge PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> respond-to-auth-challenge MFA code
  -> JWT tokens
```

The key mental model:

```text
Cognito authenticates the user.
API Gateway authorizes the request.
Lambda executes only after authorization succeeds.
CloudWatch shows what actually happened.
```

> [!important]
> The most important learning outcome is not the Chewbacca/Jedi/Sith theme. It is understanding which system owns each responsibility: Cognito issues tokens, API Gateway validates tokens, Lambda handles business logic, and CloudWatch confirms runtime behavior.

## Architecture Overview

Both versions use the same identity flow:

```text
Chewbacca CLI user
  -> Cognito User Pool
  -> USER_AUTH / SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> JWT tokens
  -> API Gateway protected route
  -> Lambda
  -> CloudWatch Logs
```

The API routes are intentionally small:

| Route | Runtime | Theme role | Purpose |
| --- | --- | --- | --- |
| `/prod/jedi` | Python | Jedi Council response path | Protected Python Lambda test route |
| `/prod/sith` | Node.js | Sith response path | Protected Node.js Lambda test route |

## HTTP API vs REST API

The lab exists in two versions so the same Cognito flow can be tested through both API Gateway models.

| Area | HTTP API Version | REST API Version |
| --- | --- | --- |
| Folder | `HTTPS/` | `REST/` |
| Project name | `chewbacca-auth-http` | `chewbacca-auth-rest` |
| API Gateway CLI namespace | `apigatewayv2` | `apigateway` |
| API Gateway type | HTTP API | REST API |
| Authorizer | JWT authorizer | Cognito User Pool authorizer |
| Barebones token used for route test | Access token | ID token |
| Route model | `GET /jedi`, `GET /sith` | Resources `/jedi`, `/sith` with GET methods |
| Deployment behavior | Auto-deploy stage | Explicit deployment after method changes |
| Custom authorizer Lambda | Not needed | Not needed |

> [!note]
> REST API Cognito authorizers behave differently depending on scopes. With no method scopes configured, API Gateway treats the supplied token as an identity token. If method-level OAuth scopes are configured, use the access token and make sure the token contains the required scope claims.

## Resource Pattern

The lab uses separate resource names so both implementations can exist in the same AWS account and region.

| Resource | HTTP API Pattern | REST API Pattern |
| --- | --- | --- |
| Project prefix | `chewbacca-auth-http` | `chewbacca-auth-rest` |
| User pool | `<PROJECT_NAME>-users` | `<PROJECT_NAME>-users` |
| App client | `<PROJECT_NAME>-cli-client` | `<PROJECT_NAME>-cli-client` |
| Jedi Lambda | `<PROJECT_NAME>-jedi-python` | `<PROJECT_NAME>-jedi-python` |
| Sith Lambda | `<PROJECT_NAME>-sith-node` | `<PROJECT_NAME>-sith-node` |
| Lambda role | `<PROJECT_NAME>-lambda-basic-role` | `<PROJECT_NAME>-lambda-basic-role` |
| Authorizer | `<PROJECT_NAME>-cognito-jwt` | `<PROJECT_NAME>-cognito-authorizer` |

## Shared Code

The lab has shared Lambda handlers and a shared helper script.

| File | Purpose |
| --- | --- |
| `shared/lambda-code/jedi_python.py` | Python Lambda route handler for `/jedi` |
| `shared/lambda-code/sith_node.js` | Node.js Lambda route handler for `/sith` |
| `shared/scripts/secret_hash.py` | Computes Cognito `SECRET_HASH` |

### Jedi Python Handler

```python
import json
from datetime import datetime, timezone


def lambda_handler(event, context):
    print("Incoming event:", json.dumps(event))

    params = event.get("queryStringParameters") or {}
    name = params.get("name", "Chewbacca")

    response = {
        "message": f"Welcome {name}. The Python Jedi Council accepts your request.",
        "runtime": "python-jedi",
        "side": "jedi",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("Response:", json.dumps(response))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response)
    }
```

### Sith Node Handler

```javascript
exports.handler = async (event) => {
    console.log("Incoming event:", JSON.stringify(event));

    const params = event.queryStringParameters || {};
    const name = params.name || "Chewbacca";

    const response = {
        message: `WELCOME ${name.toUpperCase()}. THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.`,
        runtime: "node-sith",
        side: "sith",
    };

    console.log("Response:", JSON.stringify(response));

    return {
        statusCode: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(response),
    };
};
```

## Cognito Authentication Concepts

Resource links for this section: [Cognito authentication](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html), [authentication flow methods](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-authentication-flow-methods.html), and [computing `SECRET_HASH`](https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html#cognito-user-pools-computing-secret-hash).

### `USER_AUTH`

`USER_AUTH` is the negotiated flow.

Cognito first asks:

```text
Which authentication method do you want to use?
```

The response can include:

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

This flow teaches modern identity negotiation because the client explicitly chooses the primary authentication challenge.

### `USER_PASSWORD_AUTH`

`USER_PASSWORD_AUTH` is the direct flow.

```text
USERNAME + PASSWORD + SECRET_HASH
  -> password validation
  -> MFA challenge if enabled
  -> tokens
```

It is easier for CLI testing, but it skips the `SELECT_CHALLENGE` learning step.

### `SECRET_HASH`

`SECRET_HASH` is a derived HMAC proof.

```text
username + app client ID
  -> HMAC-SHA256 using client secret
  -> base64 output
  -> SECRET_HASH
```

Cognito requires this when the app client has a client secret.

> [!warning]
> `SECRET_HASH` is not your raw client secret. It is a derived proof that lets Cognito verify that the caller knows the app client secret.

Helper script:

```python
import base64
import hashlib
import hmac
import sys


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 secret_hash.py <username> <client_id> <client_secret>", file=sys.stderr)
        sys.exit(1)

    username, client_id, client_secret = sys.argv[1:4]
    message = (username + client_id).encode("utf-8")
    key = client_secret.encode("utf-8")

    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode("utf-8")

    print(secret_hash)


if __name__ == "__main__":
    main()
```

## Console Infrastructure And CLI Authentication Workflow

The infrastructure resources should be created in the AWS Console. The command blocks below are useful as exact-value references and optional automation equivalents, but the class workflow is console setup first, then CLI authentication and route validation.

Run the CLI authentication workflow in two modes:

| Mode | Purpose | How it should feel |
| --- | --- | --- |
| Manual-first pass | Understand Cognito challenge mechanics | Read each JSON response, copy `Session` values by hand, paste MFA codes by hand, and inspect tokens before using them |
| Export-driven pass | Repeat the flow quickly | Capture responses with `export`, parse values with `jq`, and reuse tokens in curl commands |

> [!important]
> The manual pass matters. Cognito's `Session` value changes as the flow moves from `SELECT_CHALLENGE` to `PASSWORD` to `SOFTWARE_TOKEN_MFA`. Copying those values by hand once or twice makes the sequence much easier to remember later.

### 1. Export Base Values For CLI Testing

HTTP API version:

```bash
export AWS_REGION="us-west-2"
export PROJECT_NAME="chewbacca-auth-http"
```

REST API version:

```bash
export AWS_REGION="us-west-2"
export PROJECT_NAME="chewbacca-auth-rest"
```

Shared variables:

```bash
export JEDI_FUNCTION="${PROJECT_NAME}-jedi-python"
export SITH_FUNCTION="${PROJECT_NAME}-sith-node"
export LAMBDA_ROLE_NAME="${PROJECT_NAME}-lambda-basic-role"

export API_NAME="${PROJECT_NAME}-api"
export USER_POOL_NAME="${PROJECT_NAME}-users"
export USER_POOL_CLIENT_NAME="${PROJECT_NAME}-cli-client"

export TEST_USERNAME="chewbacca"
export TEST_EMAIL="chewbacca@example.com"
export TEST_PASSWORD="Wookiee#2026!"

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

### 2. Create Lambda Execution Role

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

```bash
aws iam attach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

```bash
export LAMBDA_ROLE_ARN=$(aws iam get-role \
  --role-name "$LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text)
```

### 3. Package Lambda Code

```bash
export LAB_REPO="$HOME/cognito-cli-auth-flow"
cd "$LAB_REPO/shared/lambda-code"

zip jedi-python.zip jedi_python.py
zip sith-node.zip sith_node.js
```

### 4. Create Lambda Functions

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

```bash
aws lambda create-function \
  --function-name "$SITH_FUNCTION" \
  --runtime nodejs20.x \
  --role "$LAMBDA_ROLE_ARN" \
  --handler sith_node.handler \
  --zip-file fileb://sith-node.zip \
  --region "$AWS_REGION"
```

### 5. Create Cognito User Pool

Create the user pool first with MFA off. Cognito requires SMS configuration when MFA is set to optional during `create-user-pool`, so software-token MFA is enabled after the pool exists.

Console path: **Amazon Cognito** -> **User pools** -> **Create user pool**. Use email sign-in and the password policy shown below. Leave MFA off during initial pool creation, then enable software-token MFA after the pool exists.

#### 5.1 Create The User Pool

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

#### 5.2 Enable Software Token MFA

```bash
aws cognito-idp set-user-pool-mfa-config \
  --user-pool-id "$USER_POOL_ID" \
  --mfa-configuration OPTIONAL \
  --software-token-mfa-configuration Enabled=true \
  --region "$AWS_REGION"
```

```bash
export COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"
export USER_POOL_ARN="arn:aws:cognito-idp:${AWS_REGION}:${AWS_ACCOUNT_ID}:userpool/${USER_POOL_ID}"
```

### 6. Create App Client

The app client intentionally has a secret so the lab teaches `SECRET_HASH`.

Console path: open the user pool -> **App clients** -> **Create app client**. Enable the auth flows shown below, generate a client secret, and set token expiration for the lab:

| Token | Expiration |
| --- | --- |
| Access token | `15 minutes` |
| ID token | `15 minutes` |
| Refresh token | `1 day` |

> [!note]
> The short access and ID token lifetime is intentional. It makes API Gateway's expired-token behavior easy to observe while keeping the lab quick to repeat.

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

```bash
export CLIENT_ID=$(echo "$CLIENT_JSON" | jq -r '.ClientId')
export CLIENT_SECRET=$(echo "$CLIENT_JSON" | jq -r '.ClientSecret')
echo "$CLIENT_JSON" | jq '{AccessTokenValidity,IdTokenValidity,RefreshTokenValidity,TokenValidityUnits}'
```

### 7. Create Test User

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

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEST_USERNAME" \
  --password "$TEST_PASSWORD" \
  --permanent \
  --region "$AWS_REGION"
```

### 8. Generate `SECRET_HASH`

`SECRET_HASH` is the app-client proof for clients that have a secret. Cognito expects this derived HMAC value in authentication requests so the caller proves it knows the client secret without sending the raw secret as the hash itself.

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

## MFA Enrollment

Resource links for this section: [Amazon Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html), [associate-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/associate-software-token.html), [verify-software-token](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/verify-software-token.html), and [set-user-mfa-preference](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/set-user-mfa-preference.html).

The lab uses software token MFA.

First authenticate with direct username-password auth to begin initial TOTP MFA setup:

This `initiate-auth` command uses `USER_PASSWORD_AUTH`, so the password is submitted directly in the request. Here it is only an initial setup move: the goal is to receive a short-lived access token that can authorize software-token MFA enrollment for the user.

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

> [!important]
> The temporary `ACCESS_TOKEN` in this section is only used to enroll MFA. If the token expires before MFA setup is complete, re-run the `USER_PASSWORD_AUTH` command and export a fresh token.

Associate a software token:

`associate-software-token` starts TOTP enrollment. Cognito generates and returns a private setup key, and that key becomes the shared secret between Cognito and the authenticator app.

```bash
export TOTP_SETUP_RESPONSE=$(aws cognito-idp associate-software-token \
  --access-token "$ACCESS_TOKEN" \
  --region "$AWS_REGION")
```

Print the secret code and add it to an authenticator app:

```bash
export TOTP_SECRET=$(echo "$TOTP_SETUP_RESPONSE" | jq -r '.SecretCode')
echo "$TOTP_SECRET"
```

Verify the current authenticator code:

`verify-software-token` checks a six-digit code from the authenticator app against the shared TOTP secret. A successful response marks the software token as verified for the user.

```bash
export TOTP_CODE="123456"

aws cognito-idp verify-software-token \
  --access-token "$ACCESS_TOKEN" \
  --user-code "$TOTP_CODE" \
  --friendly-device-name "Chewbacca CLI" \
  --region "$AWS_REGION"
```

Set software token MFA as preferred:

`set-user-mfa-preference` turns software-token MFA on for this user and makes it the preferred MFA method. After this, Cognito should challenge the user for a TOTP code during sign-in.

```bash
aws cognito-idp set-user-mfa-preference \
  --access-token "$ACCESS_TOKEN" \
  --software-token-mfa-settings Enabled=true,PreferredMfa=true \
  --region "$AWS_REGION"
```

## `USER_AUTH` Challenge Flow

Resource links for this section: [AWS CLI initiate-auth](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html), [AWS CLI respond-to-auth-challenge](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html), and [RespondToAuthChallenge API](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_RespondToAuthChallenge.html).

### Manual-First Pass

Run this once without assigning responses to variables. The goal is to see the challenge sequence plainly.

`USER_AUTH` starts Cognito's choice-based authentication flow. The first request identifies the user and asks Cognito which sign-in methods are available; Cognito responds with `SELECT_CHALLENGE` and a session value that preserves the challenge state.

```bash
aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION" | jq
```

Expected:

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

Copy the `Session` from the `SELECT_CHALLENGE` response.

> [!warning]
> A Cognito `Session` belongs to one specific challenge chain. If you answer `SELECT_CHALLENGE` with a session from `USER_PASSWORD_AUTH`, an older run, another app client, or another user, Cognito can return `Invalid session due to a mismatched auth flow`. Restart from `initiate-auth --auth-flow USER_AUTH` and copy the fresh `Session` from that response.

`respond-to-auth-challenge` answers Cognito's current prompt. In this step, `ANSWER="PASSWORD"` selects the password method from the available choices and supplies the user's password. If the password is accepted and MFA is enabled, Cognito returns a new `SOFTWARE_TOKEN_MFA` challenge session.

```bash
aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="$TEST_USERNAME",ANSWER="PASSWORD",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --session "PASTE_SELECT_CHALLENGE_SESSION_HERE" \
  --region "$AWS_REGION" | jq
```

Expected:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>",
  "ChallengeParameters": {
    "FRIENDLY_DEVICE_NAME": "Chewbacca CLI REST",
    "USER_ID_FOR_SRP": "chewbacca"
  }
}
```

Copy the new `Session` from the `SOFTWARE_TOKEN_MFA` response. Then use a fresh code from the authenticator app.

> [!warning]
> Do not reuse the earlier `SELECT_CHALLENGE` session for MFA. The password challenge returns a new `Session`, and that new value is the only valid handoff into `SOFTWARE_TOKEN_MFA`.

The next `respond-to-auth-challenge` call answers the MFA prompt. The session must come from the password step, and the TOTP code must be current; when Cognito accepts it, the response contains tokens instead of another challenge.

```bash
aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="$TEST_USERNAME",SOFTWARE_TOKEN_MFA_CODE="PASTE_CURRENT_MFA_CODE",SECRET_HASH="$SECRET_HASH" \
  --session "PASTE_SOFTWARE_TOKEN_MFA_SESSION_HERE" \
  --region "$AWS_REGION" | jq
```

Expected:

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

The final response contains `AccessToken`, `IdToken`, and `RefreshToken`. Copy the route token manually for the first protected-route test, then use the export path below for repeated tests.

### Export-Driven Pass

> [!important]
> The export-driven pass assumes the setup variables still exist in the shell. If you start a new terminal, reload `LAB_REPO`, `AWS_REGION`, `CLIENT_ID`, `CLIENT_SECRET`, `TEST_USERNAME`, and `TEST_PASSWORD` before generating `SECRET_HASH`. Pull `CLIENT_ID` and `CLIENT_SECRET` from the Cognito app client, and only echo a short prefix of `CLIENT_SECRET` when validating.

```bash
cd "<PATH_TO_COGNITO_CLI_AUTH_FLOW_REPO>"
export LAB_REPO="$(pwd)"
export AWS_REGION="us-west-2"
export CLIENT_ID="<CLIENT_ID>"
export CLIENT_SECRET="<CLIENT_SECRET>"
export TEST_USERNAME="chewbacca"
export TEST_PASSWORD="<USER_PASSWORD>"
```

### Step 1: Initiate `USER_AUTH`

This repeats the documented `USER_AUTH` start step, but stores the response so `jq` can extract the challenge session for the next command.

```bash
export AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_AUTH \
  --auth-parameters USERNAME="$TEST_USERNAME",SECRET_HASH="$SECRET_HASH" \
  --region "$AWS_REGION")
```

Inspect:

```bash
echo "$AUTH_RESPONSE" | jq
```

Expected:

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

### Step 2: Export Session

```bash
export SESSION=$(echo "$AUTH_RESPONSE" | jq -r '.Session')
echo "${SESSION:0:20}"
```

> [!warning]
> Cognito challenge sessions are short-lived and flow-specific. If too much time passes, or if you mix a session from `USER_PASSWORD_AUTH` with `USER_AUTH`, restart from Step 1 and replace `SESSION` with the new value.

### Step 3: Choose `PASSWORD`

This exported challenge response chooses the password method and captures Cognito's next challenge. Treat the returned `Session` as a one-use handoff into the MFA step.

```bash
export PASSWORD_CHALLENGE_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SELECT_CHALLENGE \
  --challenge-responses USERNAME="$TEST_USERNAME",ANSWER="PASSWORD",PASSWORD="$TEST_PASSWORD",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")
```

Expected:

```json
{
  "ChallengeName": "SOFTWARE_TOKEN_MFA",
  "Session": "AYABe...<SOFTWARE_TOKEN_MFA_SESSION>",
  "ChallengeParameters": {
    "FRIENDLY_DEVICE_NAME": "Chewbacca CLI REST",
    "USER_ID_FOR_SRP": "chewbacca"
  }
}
```

### Step 4: Export New Session

```bash
export SESSION=$(echo "$PASSWORD_CHALLENGE_RESPONSE" | jq -r '.Session')
```

### Step 5: Respond To MFA

This completes the exported challenge chain. The current TOTP code and latest `Session` are submitted together; success returns `AuthenticationResult` with the lab tokens.

```bash
export TOTP_CODE="123456"

export MFA_RESPONSE=$(aws cognito-idp respond-to-auth-challenge \
  --client-id "$CLIENT_ID" \
  --challenge-name SOFTWARE_TOKEN_MFA \
  --challenge-responses USERNAME="$TEST_USERNAME",SOFTWARE_TOKEN_MFA_CODE="$TOTP_CODE",SECRET_HASH="$SECRET_HASH" \
  --session "$SESSION" \
  --region "$AWS_REGION")
```

Expected:

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

> [!note]
> `ExpiresIn` reflects app client token validity. A 15-minute lab client returns `900`; a default one-hour client can return `3600`.

### Step 6: Export Tokens

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

Expected:

```text
eyJraWQiOiJNek1LXC8yZzgz
eyJraWQiOiJnVkkrSDRcL0Ja
eyJjdHkiOiJKV1QiLCJlbmMi
```

> [!important]
> Cognito tokens expire. If API Gateway returns `{"message":"The incoming token has expired"}`, the authorizer is doing its job and Lambda was not invoked. Run the auth flow again, export a fresh route token, and retry the request.

## Token Handling

| Token | Meaning | Lab use |
| --- | --- | --- |
| `ACCESS_TOKEN` | API authorization token | HTTP API JWT authorizer test |
| `ID_TOKEN` | User identity/profile token | REST API no-scope Cognito authorizer test |
| `REFRESH_TOKEN` | Used to obtain fresh tokens | Do not send to API Gateway |

> [!tip]
> If the REST API method has no OAuth scopes configured, test with `ID_TOKEN`. If method scopes are configured, test with `ACCESS_TOKEN` and confirm the required scope appears in the token.

### Token And Session Expiration

| Expiring value | Where it appears | What to do |
| --- | --- | --- |
| MFA enrollment `ACCESS_TOKEN` | `associate-software-token`, `verify-software-token`, `set-user-mfa-preference` | Re-run the direct `USER_PASSWORD_AUTH` command and export a new temporary `ACCESS_TOKEN` |
| Cognito challenge `SESSION` | `SELECT_CHALLENGE` and `SOFTWARE_TOKEN_MFA` responses | Restart the `USER_AUTH` flow from `initiate-auth` |
| API route token | HTTP API `ACCESS_TOKEN` or REST API `ID_TOKEN` | Expires after 15 minutes; re-run the auth flow, export a fresh token, and retry curl |
| Refresh token | Token renewal workflows outside this barebones lab | Keep private; do not send it to API Gateway |

## HTTP API Protected Route Pattern

Resource links for this section: [HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html), [HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html), and [HTTP API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html).

HTTP API uses `apigatewayv2` for CLI reference, but the intended lab setup is console-first.

Console path: **API Gateway** -> **Create API** -> **HTTP API** -> create the API from `API_NAME`, add Lambda integrations for `/jedi` and `/sith`, create the `prod` stage, then attach a JWT authorizer.

Equivalent CLI reference:

```bash
export API_ID=$(aws apigatewayv2 create-api \
  --name "$API_NAME" \
  --protocol-type HTTP \
  --query 'ApiId' \
  --output text \
  --region "$AWS_REGION")
```

Create JWT authorizer:

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

Test:

This request sends the Cognito access token in the `Authorization` header. HTTP API validates the JWT before Lambda runs, so a successful response proves both the token and route authorizer are wired correctly.

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

> [!note]
> If HTTP API returns `{"message":"The incoming token has expired"}`, export a fresh `ACCESS_TOKEN` before retesting. API Gateway rejected the request before Lambda ran.

Manual token test:

This is the same test without shell variables. Pasting the access token by hand is useful during the first pass because it reinforces which token belongs in the bearer header.

```bash
curl -i \
  -H "Authorization: Bearer PASTE_ACCESS_TOKEN_HERE" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Key behavior:

```text
Missing or invalid token -> 401
Valid access token -> Lambda runs
```

## REST API Protected Route Pattern

Resource links for this section: [REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html), [Cognito user pool authorizers for REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html), and [REST API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html).

REST API uses `apigateway` for CLI reference, but the intended lab setup is console-first.

Console path: **API Gateway** -> **Create API** -> **REST API** -> create the API from `API_NAME`, add `/jedi` and `/sith` resources, add `GET` methods, enable Lambda proxy integration, deploy to `prod`, then attach the Cognito User Pool authorizer.

Equivalent CLI reference:

```bash
export REST_API_ID=$(aws apigateway create-rest-api \
  --name "$API_NAME" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text \
  --region "$AWS_REGION")
```

Create Cognito authorizer:

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

> [!note]
> If API Gateway returns `Authorizer name must be unique`, the authorizer already exists for this REST API. Reuse the existing authorizer ID instead of creating a duplicate.

Attach authorizer to method:

```bash
aws apigateway update-method \
  --rest-api-id "$REST_API_ID" \
  --resource-id "$JEDI_RESOURCE_ID" \
  --http-method GET \
  --patch-operations \
    op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
    op=replace,path=/authorizerId,value="$COGNITO_AUTHORIZER_ID" \
  --region "$AWS_REGION"
```

Redeploy after method changes:

```bash
aws apigateway create-deployment \
  --rest-api-id "$REST_API_ID" \
  --stage-name prod \
  --description "Protected Jedi and Sith routes with Cognito authorizer" \
  --region "$AWS_REGION"
```

Test:

This request sends the Cognito ID token in the `Authorization` header. In the barebones REST flow, no method scopes are configured, so the Cognito user-pool authorizer can validate the identity token and allow the Lambda integration.

```bash
curl -i \
  -H "Authorization: Bearer $ID_TOKEN" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

> [!note]
> If REST API returns `{"message":"The incoming token has expired"}`, export a fresh `ID_TOKEN` before retesting. API Gateway rejected the request before Lambda ran.

Manual token test:

This is the same REST test without shell variables. Pasting the ID token by hand makes the token choice explicit before switching back to the export-driven path.

```bash
curl -i \
  -H "Authorization: Bearer PASTE_ID_TOKEN_HERE" \
  "${API_ENDPOINT}/prod/jedi?name=Chewbacca"
```

Key behavior:

```text
Missing or invalid token -> 401
Valid ID token on no-scope method -> Lambda runs
REST API method changes require redeployment
```

## Hosted UI Connection

Resource links for this section: [Cognito managed login and Hosted UI](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-hosted-ui-user-experience.html), [authorization endpoint](https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html), and [token endpoint](https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html).

This lab is CLI-first, but the same Cognito user pool concepts show up in Hosted UI flows.

Hosted UI flow:

```text
Browser
  -> Cognito Hosted UI /login
  -> Authorization code
  -> Callback endpoint
  -> Server-side token exchange
  -> Application session
```

CLI flow:

```text
Terminal
  -> initiate-auth
  -> respond-to-auth-challenge
  -> tokens directly returned to CLI
```

The CLI flow is better for understanding raw challenge mechanics. Hosted UI is better for browser applications because users do not hand passwords directly to your application code.

## Security Considerations

- Do not commit real Cognito client secrets.
- Do not commit generated JWTs.
- Use `SECRET_HASH` only as a derived proof, not as a replacement for secret storage.
- Keep `REFRESH_TOKEN` private.
- Prefer Hosted UI or SRP-based flows for browser-facing applications.
- Use least-privilege Lambda roles.
- Check CloudWatch logs, but do not print secrets or full tokens in production logs.
- Use separate project prefixes for HTTP API and REST API labs.

## Debugging Checkpoints

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unable to verify secret hash` | Username, client ID, or client secret mismatch | Recompute `SECRET_HASH` with exact username and client values |
| `InvalidParameterException` for `USER_AUTH` | App client does not allow `ALLOW_USER_AUTH` | Recreate/update client explicit auth flows |
| `Invalid session due to a mismatched auth flow` | The `Session` came from the wrong auth flow, an older challenge chain, another app client, or another user | Restart from `initiate-auth --auth-flow USER_AUTH`, copy the fresh `SELECT_CHALLENGE` session, then use the new MFA session returned by the password step |
| `NotAuthorizedException` | Wrong password, expired session, wrong secret hash | Restart auth from `initiate-auth` |
| `CodeMismatchException` | MFA code expired or copied wrong | Wait for a fresh authenticator code |
| `{"message":"The incoming token has expired"}` | API Gateway received an expired JWT | Re-run the auth flow and export a fresh route token |
| HTTP API returns `401` | Missing/expired access token or wrong issuer/audience | Re-export `ACCESS_TOKEN` and verify authorizer config |
| REST API returns `401` | Used access token on no-scope method, wrong user pool ARN, or stale deployment | Use `ID_TOKEN`, confirm authorizer, redeploy |
| `Authorizer name must be unique` | The REST API already has an authorizer with that name | Reuse the existing authorizer ID instead of creating a duplicate |
| Lambda never logs | API Gateway rejected request before invocation | Check authorizer result before debugging Lambda |
| REST method still public | Method was updated but stage was not redeployed | Run `create-deployment` again |

## Validation Tasks

- [ ] Explain why `SECRET_HASH` exists.
- [ ] Generate a valid `SECRET_HASH`.
- [ ] Run the manual-first `USER_AUTH` flow and observe `SELECT_CHALLENGE`.
- [ ] Copy the first `Session` value by hand into the `PASSWORD` challenge.
- [ ] Copy the second `Session` value by hand into the `SOFTWARE_TOKEN_MFA` challenge.
- [ ] Complete `SOFTWARE_TOKEN_MFA` with a fresh authenticator code.
- [ ] Export `ACCESS_TOKEN`, `ID_TOKEN`, and `REFRESH_TOKEN`.
- [ ] Call an HTTP API protected route with `ACCESS_TOKEN`.
- [ ] Call a REST API protected route with `ID_TOKEN`.
- [ ] Confirm Lambda logs appear only after authorization succeeds.
- [ ] Explain why REST API changes require redeployment.

## Concept Checks

**Q: What does Cognito own in this lab?**  
A: User authentication, challenge negotiation, MFA validation, and token issuance.

**Q: What does API Gateway own?**  
A: Request routing and token validation before Lambda invocation.

**Q: Why does Lambda not log when auth fails?**  
A: API Gateway rejects the request before invoking Lambda.

**Q: Why use `SECRET_HASH`?**  
A: To prove knowledge of the app client secret without sending the raw secret as a challenge answer.

**Q: Why does REST use `ID_TOKEN` in this barebones lab?**  
A: With no OAuth scopes configured, REST API Cognito authorizers treat the supplied token as an identity token.

**Q: When would REST use `ACCESS_TOKEN` instead?**  
A: When method-level OAuth scopes are configured.

## Strategic Takeaways

- `USER_AUTH` teaches authentication negotiation.
- `USER_PASSWORD_AUTH` is simpler but hides the challenge-selection step.
- Manual-first testing makes the changing Cognito `Session` values visible before exports hide the mechanics.
- `SECRET_HASH` is application-client proof, not user proof.
- MFA adds a second challenge after the primary factor.
- Access tokens and ID tokens are not interchangeable in every API Gateway mode.
- HTTP API and REST API can protect the same Lambda routes, but their authorizer models differ.
- The cleanest troubleshooting path is always: token claims, authorizer config, route/method config, Lambda logs.

## Study References

- [AWS CLI initiate-auth](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/initiate-auth.html)
- [AWS CLI respond-to-auth-challenge](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/respond-to-auth-challenge.html)
- [Amazon Cognito authentication flows](https://docs.aws.amazon.com/cognito/latest/developerguide/authentication.html)
- [Amazon Cognito MFA](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
- [API Gateway HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
- [API Gateway REST API Cognito authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
- [REST API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)
- [HTTP API Lambda proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)

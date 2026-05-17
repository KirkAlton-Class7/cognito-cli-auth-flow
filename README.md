# Chewbacca Cognito CLI Auth Flow

Basic AWS lab for learning Cognito authentication flows, JWT validation, API Gateway, and Lambda with a Chewbacca, Jedi, and Sith theme.

This repo is intentionally smaller than Tawny Port. It isolates the authentication mechanics so you can see how Cognito behaves before putting the pattern inside a larger application.

## Implementation

The lab demonstrates the same Cognito identity flow across two API Gateway implementations:

* The AWS Console is used to create the user pool, app client, Lambda functions, API Gateway routes, and authorizers.
* The CLI walks through `USER_AUTH`, `SELECT_CHALLENGE`, `PASSWORD`, `SOFTWARE_TOKEN_MFA`, manual token inspection, exported token reuse, and route testing.
* API Gateway protects simple Jedi and Sith Lambda routes after the console infrastructure is in place.
* Lambda only runs after API Gateway accepts the Cognito token.
* CloudWatch proves whether the request actually reached the function.

Start with the API Gateway style you want to practice:

* [HTTPS Version](HTTPS/README.md) (HTTP API JWT authorizer)
* [REST Version](REST/README.md) (REST API Cognito User Pool authorizer)

> [!IMPORTANT]
> Use separate project names when running both versions. The runbooks already do this with `chewbacca-auth-http` and `chewbacca-auth-rest`, so both labs can exist in the same AWS account and region.

> [!NOTE]
> The commands assume the repo lives at `"$HOME/cognito-cli-auth-flow"`. If you clone it somewhere else, set `LAB_REPO` to that path before packaging Lambda code or running helper scripts.

## Platform Overview

The flow stays the same in both versions:

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

| Route | Runtime | Theme role |
| --- | --- | --- |
| `/prod/jedi` | Python | Jedi Council response path |
| `/prod/sith` | Node.js | Sith response path |

## HTTPS vs REST

Both versions preserve the same user, challenge, MFA, and token flow. The difference is how API Gateway validates the token.

| Area | HTTPS Version | REST Version |
| --- | --- | --- |
| API Gateway type | HTTP API | REST API |
| Authorizer type | HTTP API JWT authorizer | REST API Cognito User Pool authorizer |
| Token used in the barebones route test | Cognito access token | Cognito ID token |
| CLI namespace | `apigatewayv2` | `apigateway` |
| Route model | Routes such as `GET /jedi` | Resources and methods such as `/jedi` + `GET` |
| Deployment behavior | Auto-deploy stage | Explicit deployment required after method changes |
| Custom authorizer Lambda | Not needed | Not needed for this Cognito-only lab |

> [!NOTE]
> A Lambda authorizer is not required here. Cognito issues the token, and both API Gateway implementations can validate Cognito tokens natively. Use a Lambda authorizer only when you need custom policy logic or a non-Cognito identity provider.

## Build Mode

Use the **AWS Console** for infrastructure creation:

```text
IAM role
Lambda functions
Cognito user pool and app client
API Gateway API, routes/resources, integrations, stages, and authorizers
```

Use the **CLI** for the authentication workflow and validation. Run the auth flow more than one way on purpose:

```text
Manual pass:
  read each Cognito response
  copy Session values by hand
  paste MFA codes by hand
  observe where tokens appear

Export pass:
  export generated IDs
  generate SECRET_HASH
  export Session and JWT values
  repeat curl route tests quickly
```

> [!IMPORTANT]
> Do the manual CLI pass first. Copying the `Session` value from `SELECT_CHALLENGE` into the next command, then copying the new `Session` into the MFA command, is the part that makes Cognito's challenge flow click. The export-based path is included after that so you can repeat the lab without turning every run into archaeology.

## Repository Structure

```text
cognito-cli-auth-flow/
├── HTTPS/
│   ├── README.md
│   └── docs/
│       └── cognito-auth-flow-https-runbook.md
├── REST/
│   ├── README.md
│   └── docs/
│       └── cognito-auth-flow-rest-runbook.md
└── shared/
    ├── lambda-code/
    │   ├── jedi_python.py
    │   └── sith_node.js
    └── scripts/
        └── secret_hash.py
```

## Shared Code

The Lambda and helper script files are shared across both implementations:

| Path | Purpose |
| --- | --- |
| [shared/lambda-code/jedi_python.py](shared/lambda-code/jedi_python.py) | Python Jedi route handler |
| [shared/lambda-code/sith_node.js](shared/lambda-code/sith_node.js) | Node.js Sith route handler |
| [shared/scripts/secret_hash.py](shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper for app clients with secrets |

## Learning Outcome

You are finished when you can explain this chain confidently:

```text
SECRET_HASH proves the app client secret
USER_AUTH starts negotiation
SELECT_CHALLENGE lets the client choose PASSWORD
PASSWORD validates the primary factor
SOFTWARE_TOKEN_MFA validates the second factor
Cognito issues JWT tokens
API Gateway validates the access token
Lambda runs only after authorization succeeds
CloudWatch shows what actually happened
```

# Chewbacca Cognito CLI Auth Flow

Basic AWS CLI lab for learning Cognito authentication flows, JWT validation, API Gateway, and Lambda with a Chewbacca, Jedi, and Sith theme.

This repo is intentionally smaller than Tawny Port. It isolates the authentication mechanics so you can see how Cognito behaves before putting the pattern inside a larger application.

## Implementation

The lab demonstrates the same Cognito identity flow across two API Gateway implementations:

* Cognito owns the user pool, app client, password auth, MFA challenge, and JWT issuance.
* The CLI walks through `USER_AUTH`, `SELECT_CHALLENGE`, `PASSWORD`, and `SOFTWARE_TOKEN_MFA`.
* API Gateway protects simple Jedi and Sith Lambda routes.
* Lambda only runs after API Gateway accepts the Cognito token.
* CloudWatch proves whether the request actually reached the function.

Start with the API Gateway style you want to practice:

* [HTTPS Version](HTTPS/README.md) (HTTP API JWT authorizer)
* [REST Version](REST/README.md) (REST API Cognito User Pool authorizer)

> [!IMPORTANT]
> Use separate project names when running both versions. The runbooks already do this with `chewbacca-auth-http` and `chewbacca-auth-rest`, so both labs can exist in the same AWS account and region.

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

You are finished when you can explain this chain without looking:

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

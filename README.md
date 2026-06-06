# Cognito Auth Flow

AWS Cognito authentication flow reference using API Gateway, Lambda, JWT authorizers, software-token MFA, and small themed Jedi/Sith route handlers.

This repository keeps the application intentionally small so the authentication boundary stays visible. The same Cognito identity flow is implemented through both API Gateway HTTP API and REST API patterns, with separate runbooks, lab walkthroughs, and teardown references.

## What This Demonstrates

- Chewbacca test user
- Cognito User Pool
- app clients for SECRET_HASH, managed login, and token helper scripts
- USER_AUTH / SELECT_CHALLENGE
- PASSWORD
- SOFTWARE_TOKEN_MFA
- Cognito JWT tokens
- API Gateway protected route
- Lambda
- CloudWatch Logs

The protected routes are intentionally simple:

| Route | Runtime | Purpose |
| --- | --- | --- |
| `/prod/jedi` | Python | Validates the Python Lambda route behind Cognito authorization |
| `/prod/sith` | Node.js | Validates the Node.js Lambda route behind Cognito authorization |

## Implementations

Start with the API Gateway implementation you want to build:

| Path | Use |
| --- | --- |
| [HTTPS](HTTPS/README.md) | HTTP API implementation using a Cognito JWT authorizer |
| [REST](REST/README.md) | REST API implementation using a Cognito User Pool authorizer |
| [Token Detector](deploy-token-detector/README.md) | Token-use tracking extension after a base auth flow exists |

## HTTPS vs REST

Both implementations preserve the same Cognito user, challenge, MFA, and token flow. The main difference is how API Gateway models routes and validates tokens.

| Area | HTTPS | REST |
| --- | --- | --- |
| API Gateway type | HTTP API | REST API |
| Authorizer type | JWT authorizer | Cognito User Pool authorizer |
| CLI namespace | `apigatewayv2` | `apigateway` |
| Route model | Routes such as `GET /jedi` | Resources and methods such as `/jedi` + `GET` |
| Deployment behavior | Auto-deploy stage | Explicit deployment after method or authorizer changes |
| Protected-route token | Cognito access token | Cognito access token when method authorization scopes are configured |
| Custom authorizer Lambda | Not required | Not required |

> [!NOTE]
> Cognito issues the token, and both API Gateway implementations can validate Cognito tokens natively. A Lambda authorizer is only needed when custom policy logic or a non-Cognito identity provider is required.

## Documentation

Use the runbooks for the concise deployment workflow:

| Implementation | CLI Runbook | Console Runbook | Teardown |
| --- | --- | --- | --- |
| HTTPS | [RUNBOOK-CLI.md](HTTPS/docs/RUNBOOK-CLI.md) | [RUNBOOK-CONSOLE.md](HTTPS/docs/RUNBOOK-CONSOLE.md) | [TEARDOWN_HTTPS.md](HTTPS/docs/TEARDOWN_HTTPS.md) |
| REST | [RUNBOOK-CLI.md](REST/docs/RUNBOOK-CLI.md) | [RUNBOOK-CONSOLE.md](REST/docs/RUNBOOK-CONSOLE.md) | [TEARDOWN_REST.md](REST/docs/TEARDOWN_REST.md) |

Use the lab walkthroughs for screenshots, deeper explanations, and step-by-step challenge-flow practice:

| Area | Guided Lab |
| --- | --- |
| HTTPS auth flow | [HTTPS Lab README](HTTPS/labs/cognito-auth-flow-HTTPS/LAB-README.md) |
| REST auth flow | [REST Lab README](REST/labs/cognito-auth-flow-REST/LAB-README.md) |
| Token detector extension | [Unused Token Detector Lab README](deploy-token-detector/labs/token-detector/LAB-README.md) |

## Deployment Methods

Each implementation supports two infrastructure deployment methods:

| Deployment | Best For |
| --- | --- |
| CLI | Repeatable rebuilds and direct AWS API visibility |
| Console | Visual confirmation of service boundaries and AWS configuration screens |

Both deployment methods validate the deployed flow with token helper scripts, Cognito-issued JWTs, protected route calls, and CloudWatch logs.

## Repository Structure

```text
cognito-cli-auth-flow/
├── deploy-token-detector/
│   ├── README.md
│   ├── docs/
│   │   ├── deploy-token-detector-runbook.md
│   │   ├── TEARDOWN_HTTPS.md
│   │   └── TEARDOWN_REST.md
│   ├── labs/token-detector/
│   ├── lambda-code/
│   └── scripts/
├── HTTPS/
│   ├── README.md
│   ├── docs/
│   │   ├── RUNBOOK-CLI.md
│   │   ├── RUNBOOK-CONSOLE.md
│   │   └── TEARDOWN_HTTPS.md
│   └── labs/cognito-auth-flow-HTTPS/
├── REST/
│   ├── README.md
│   ├── architecture.md
│   ├── docs/
│   │   ├── RUNBOOK-CLI.md
│   │   ├── RUNBOOK-CONSOLE.md
│   │   └── TEARDOWN_REST.md
│   └── labs/cognito-auth-flow-REST/
├── assets/images/
├── requirements.txt
└── shared/
    ├── lambda-code/
    │   ├── jedi_python.py
    │   └── sith_node.js
    └── scripts/
        ├── secret_hash.py
        ├── easier_get_token.py
        └── flavor_get_token.py
```

## Shared Code

| Path | Purpose |
| --- | --- |
| [shared/lambda-code/jedi_python.py](shared/lambda-code/jedi_python.py) | Python Jedi route handler |
| [shared/lambda-code/sith_node.js](shared/lambda-code/sith_node.js) | Node.js Sith route handler |
| [shared/scripts/secret_hash.py](shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper for app clients with secrets |
| [shared/scripts/easier_get_token.py](shared/scripts/easier_get_token.py) | Direct `USER_PASSWORD_AUTH` token helper for a public no-secret app client |
| [shared/scripts/flavor_get_token.py](shared/scripts/flavor_get_token.py) | Token helper that decodes claims and prints Jedi/Sith curl examples |
| [requirements.txt](requirements.txt) | Python dependency list for token helper scripts |

## Operating Notes

Use separate project names when running both API Gateway implementations in the same AWS account and region. The provided docs use `chewbacca-auth-http` for HTTP API and `chewbacca-auth-rest` for REST API.

The examples assume the repository is available at `"$HOME/cognito-cli-auth-flow"` or that `REPO_ROOT` points to the actual clone path before packaging Lambda code or running token helper scripts.

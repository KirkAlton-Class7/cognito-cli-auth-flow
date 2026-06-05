# Cognito Auth Flow

Basic AWS lab for learning Cognito authentication flows, JWT validation, API Gateway, and Lambda with a Chewbacca, Jedi, and Sith theme.

This repo is intentionally smaller than Tawny Port. It isolates the authentication mechanics so you can see how Cognito behaves before putting the pattern inside a larger application.

## Implementation

The lab demonstrates the same Cognito identity flow across two API Gateway implementations:

* The runbooks and labs include Console-first and CLI-first paths for creating user pools, app clients, Lambda functions, API Gateway routes/resources, and authorizers.
* The CLI walks through `USER_AUTH`, `SELECT_CHALLENGE`, `PASSWORD`, `SOFTWARE_TOKEN_MFA`, manual token inspection, exported token reuse, helper-script token retrieval, and route testing.
* API Gateway protects simple Jedi and Sith Lambda routes after the infrastructure is in place.
* Lambda only runs after API Gateway accepts the Cognito token.
* CloudWatch proves whether the request actually reached the function.

Start with the API Gateway style you want to practice:

* [HTTPS Version](HTTPS/README.md) (HTTP API JWT authorizer)
* [REST Version](REST/README.md) (REST API Cognito User Pool authorizer)
* [Token Detector](deploy-token-detector/README.md) (token-use tracking after a base auth flow exists)
* [Unused Token Detector Lab](deploy-token-detector/labs/token-detector/LAB-README.md) (guided editing path for the token detector)

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
| Token used in protected route tests | Cognito access token | Cognito access token when authorization scopes are configured |
| CLI namespace | `apigatewayv2` | `apigateway` |
| Route model | Routes such as `GET /jedi` | Resources and methods such as `/jedi` + `GET` |
| Deployment behavior | Auto-deploy stage | Explicit deployment required after method changes |
| Custom authorizer Lambda | Not needed | Not needed for this Cognito-only lab |

> [!NOTE]
> A Lambda authorizer is not required here. Cognito issues the token, and both API Gateway implementations can validate Cognito tokens natively. Use a Lambda authorizer only when you need custom policy logic or a non-Cognito identity provider.

## Build Mode

Use either the **AWS Console** or the matching **CLI runbook** for infrastructure creation:

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

Token helper script pass:
  create or use a public no-secret app client
  set up a local Python venv
  run easier_get_token.py for direct token retrieval
  run flavor_get_token.py for decoded claims and curl examples
```

> [!IMPORTANT]
> Do the manual CLI pass first. Copying the `Session` value from `SELECT_CHALLENGE` into the next command, then copying the new `Session` into the MFA command, is the part that makes Cognito's challenge flow click. The export-based path is included after that so you can repeat the lab without turning every run into archaeology.

## Repository Structure

```text
cognito-cli-auth-flow/
├── deploy-token-detector/
│   ├── README.md
│   ├── docs/
│   │   ├── deploy-token-detector-runbook.md
│   │   ├── TEARDOWN_HTTPS.md
│   │   └── TEARDOWN_REST.md
│   ├── labs/
│   │   └── token-detector/
│   │       ├── LAB-README.md
│   │       ├── lab-docs/
│   │       ├── quick-deployment/
│   │       └── sandbox/
│   ├── lambda-code/
│   └── scripts/
├── HTTPS/
│   ├── README.md
│   ├── docs/
│   │   ├── RUNBOOK-CLI.md
│   │   ├── RUNBOOK-CONSOLE.md
│   │   └── TEARDOWN_HTTPS.md
│   └── labs/
│       └── cognito-auth-flow-HTTPS/
│           ├── LAB-README.md
│           └── lab-docs/
│               ├── LAB-CLI.md
│               └── LAB-CONSOLE.md
├── REST/
│   ├── README.md
│   ├── architecture.md
│   ├── docs/
│   │   ├── RUNBOOK-CLI.md
│   │   ├── RUNBOOK-CONSOLE.md
│   │   └── TEARDOWN_REST.md
│   └── labs/
│       └── cognito-auth-flow-REST/
│           ├── LAB-README.md
│           └── lab-docs/
│               ├── LAB-CLI.md
│               └── LAB-CONSOLE.md
└── shared/
    ├── lambda-code/
    │   ├── jedi_python.py
    │   └── sith_node.js
    └── scripts/
        ├── requirements.txt
        ├── secret_hash.py
        ├── easier_get_token.py
        └── flavor_get_token.py
```

## Shared Code

The Lambda and helper script files are shared across both implementations:

| Path | Purpose |
| --- | --- |
| [shared/lambda-code/jedi_python.py](shared/lambda-code/jedi_python.py) | Python Jedi route handler |
| [shared/lambda-code/sith_node.js](shared/lambda-code/sith_node.js) | Node.js Sith route handler |
| [shared/scripts/secret_hash.py](shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper for app clients with secrets |
| [shared/scripts/easier_get_token.py](shared/scripts/easier_get_token.py) | Direct `USER_PASSWORD_AUTH` token helper for a public no-secret app client |
| [shared/scripts/flavor_get_token.py](shared/scripts/flavor_get_token.py) | Token helper that decodes claims and prints Jedi/Sith curl examples |
| [shared/scripts/requirements.txt](shared/scripts/requirements.txt) | Python dependency list for the helper-script venv |

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

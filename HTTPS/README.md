# Cognito Auth Flow - HTTPS Deployment

HTTP API implementation of the Cognito auth-flow lab.<br>
View the REST deployment [here](../REST/README.md) if you prefer that implementation.<br><br>

This deployment uses API Gateway **HTTP API** routes with a built-in JWT authorizer. Use the CLI-first or Console-first deployment to build the infrastructure, then use the CLI for the Cognito challenge flow, token handling, and protected route tests.

The runbook intentionally progresses through several CLI passes:

* Manual-first pass: read each Cognito JSON response, copy `Session` values by hand, and paste the MFA code yourself.
* Export-driven pass: export sessions and tokens so you can repeat the flow quickly after you understand it.
* Helper-script pass: use a public no-secret app client with `easier_get_token.py`, then use `flavor_get_token.py` for decoded claims and ready-made route tests.

> [!IMPORTANT]
> This folder documents the HTTP API implementation. Keep its API ID, stage, routes, and cleanup variables separate from the REST implementation.

## Documentation

| Document | Use |
| --- | --- |
| [Architecture](docs/architecture.md) | HTTP API request flow and authorization boundary |
| [Runbook - CLI](docs/RUNBOOK-CLI.md) | Build and validate the HTTPS deployment primarily with AWS CLI commands |
| [Runbook - Console](docs/RUNBOOK-CONSOLE.md) | Build the HTTPS deployment primarily in the AWS Console with CLI validation |
| [Lab - CLI](labs/cognito-auth-flow-HTTPS/lab-docs/LAB-CLI.md) | Guided CLI-first deployment lab with deeper explanations |
| [Lab - Console](labs/cognito-auth-flow-HTTPS/lab-docs/LAB-CONSOLE.md) | Guided Console-first deployment lab with deeper explanations |
| [Teardown](docs/TEARDOWN_HTTPS.md) | Remove only the base HTTPS deployment |
| [REST Deployment](../REST/README.md) | Companion REST API deployment |
| [Shared Lambda Code](../shared/lambda-code/) | Jedi and Sith Lambda handlers |
| [Secret Hash Helper](../shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper |
| [Token Helpers](../shared/scripts/) | `easier_get_token.py`, `flavor_get_token.py`, and venv requirements |
| [Token Detector](../deploy-token-detector/README.md) | Token-use tracking add-on after the base auth flow exists |

## Deployment Components

- Cognito user pool and app clients
- Chewbacca test user with software-token MFA enabled
- Jedi Python Lambda
- Sith Node.js Lambda
- HTTP API routes
- HTTP API JWT authorizer
- CloudWatch logs for Lambda and API validation

## Authentication Flow

- Chewbacca authenticates with Cognito.
- Cognito negotiates password and software-token MFA challenges.
- Cognito issues JWT tokens.
- API Gateway validates the access token with the HTTP API JWT authorizer.
- Authorized requests invoke the Jedi and Sith Lambda routes.

## Get Started

Use either HTTPS runbook in `docs/` to build the deployment, or start from the [HTTPS lab README](labs/cognito-auth-flow-HTTPS/LAB-README.md) when you want the fuller lab walkthrough. Work from `"$HOME/cognito-cli-auth-flow"` when packaging Lambda code or running helper scripts.

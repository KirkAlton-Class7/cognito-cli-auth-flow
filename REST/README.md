# Cognito Auth Flow - REST Deployment

REST API implementation of the Cognito auth-flow deployment.<br>
View the HTTPS deployment [here](../HTTPS/README.md) if you prefer that implementation.<br><br>

This deployment uses API Gateway **REST API** resources and methods with a native Cognito User Pool authorizer. Use the CLI-first or Console-first deployment to build the infrastructure, then use the CLI for the Cognito challenge flow, token handling, and protected route tests.

The runbook intentionally progresses through several CLI passes:

* Manual-first pass: read each Cognito JSON response, copy `Session` values by hand, and paste the MFA code yourself.
* Export-driven pass: export sessions and tokens so you can repeat the flow quickly after you understand it.
* Token helper script pass: use a public no-secret app client with `easier_get_token.py`, then use `flavor_get_token.py` for decoded claims and ready-made route tests.

> [!IMPORTANT]
> This folder documents the REST API implementation. REST APIs require an explicit deployment after method or authorizer changes.

## Documentation

| Document | Use |
| --- | --- |
| [Architecture](architecture.md) | REST API request flow and authorization boundary |
| [Runbook - CLI](docs/RUNBOOK-CLI.md) | Build and validate the REST deployment primarily with AWS CLI commands |
| [Runbook - Console](docs/RUNBOOK-CONSOLE.md) | Build the REST deployment primarily in the AWS Console with CLI validation |
| [Lab - CLI](labs/cognito-auth-flow-REST/lab-docs/LAB-CLI.md) | Guided CLI-first deployment lab with deeper explanations |
| [Lab - Console](labs/cognito-auth-flow-REST/lab-docs/LAB-CONSOLE.md) | Guided Console-first deployment lab with deeper explanations |
| [Teardown](docs/TEARDOWN_REST.md) | Remove only the base REST deployment |
| [HTTPS Deployment](../HTTPS/README.md) | Companion HTTP API deployment |
| [Shared Lambda Code](../shared/lambda-code/) | Jedi and Sith Lambda handlers |
| [Secret Hash Helper](../shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper |
| [Token Helpers](../shared/scripts/) | `easier_get_token.py`, `flavor_get_token.py`, and venv requirements |
| [Token Detector](../deploy-token-detector/README.md) | Token-use tracking add-on after the base auth flow exists |

## Deployment Components

- Cognito user pool and app clients
- Chewbacca test user with software-token MFA enabled
- Jedi Python Lambda
- Sith Node.js Lambda
- REST API resources and GET methods
- REST API Cognito User Pool authorizer
- CloudWatch logs for Lambda and API validation

## Authentication Flow

- Chewbacca authenticates with Cognito.
- Cognito negotiates password and software-token MFA challenges.
- Cognito issues JWT tokens.
- API Gateway validates the access token with the REST API Cognito User Pool authorizer.
- Authorized requests invoke the Jedi and Sith Lambda routes.

## Get Started

Use either REST runbook in `docs/` to build the deployment, or start from the [REST lab README](labs/cognito-auth-flow-REST/LAB-README.md) when you want the fuller lab walkthrough. Work from `"$HOME/cognito-cli-auth-flow"` when packaging Lambda code or running helper scripts.

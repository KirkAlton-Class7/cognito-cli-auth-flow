# Chewbacca Cognito Auth Flow - HTTPS Version

HTTP API implementation of the Chewbacca Cognito CLI auth-flow lab.<br>
View the REST version [here](../REST/README.md) if you prefer that implementation.<br><br>

This version uses API Gateway **HTTP API** routes with a built-in JWT authorizer. Build the infrastructure in the AWS Console, then use the CLI for the Cognito challenge flow, token handling, and protected route tests.

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
| [Full Runbook](docs/cognito-auth-flow-https-runbook.md) | Console infrastructure guide with CLI authentication and protected route validation |
| [Teardown](docs/TEARDOWN_HTTPS.md) | Remove only the base HTTPS lab infrastructure |
| [REST Version](../REST/README.md) | Companion REST API implementation |
| [Shared Lambda Code](../shared/lambda-code/) | Jedi and Sith Lambda handlers |
| [Secret Hash Helper](../shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper |
| [Token Helpers](../shared/scripts/) | `easier_get_token.py`, `flavor_get_token.py`, and venv requirements |
| [Token Detector](../deploy-token-detector/README.md) | Token-use tracking add-on after the base auth flow exists |

## Architecture Summary

```text
Chewbacca CLI
  -> Cognito USER_AUTH
  -> SELECT_CHALLENGE
  -> SOFTWARE_TOKEN_MFA
  -> Access token
  -> HTTP API JWT authorizer
  -> Jedi/Sith Lambda
```

## Get Started

Use the [HTTPS runbook](docs/cognito-auth-flow-https-runbook.md) to build the infrastructure in the AWS Console and validate the authentication flow from the CLI. Work from `"$HOME/cognito-cli-auth-flow"` when packaging Lambda code or running helper scripts:

* Cognito user pool and app client
* Chewbacca test user with software token MFA
* Jedi Python Lambda
* Sith Node.js Lambda
* HTTP API routes
* HTTP API JWT authorizer
* End-to-end protected route tests

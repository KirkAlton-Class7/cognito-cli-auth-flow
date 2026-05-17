# Chewbacca Cognito Auth Flow - HTTPS Version

HTTP API implementation of the Chewbacca Cognito CLI auth-flow lab.<br>
View the REST version [here](../REST/README.md) if you prefer that implementation.<br><br>

This version uses API Gateway **HTTP API** routes with a built-in JWT authorizer. The Cognito CLI flow is the same as the REST version: Chewbacca signs in through Cognito CLI commands, completes MFA, exports an access token, and uses it to reach protected Jedi and Sith Lambda routes.

> [!IMPORTANT]
> This folder documents the HTTP API implementation. Keep its API ID, stage, routes, and cleanup variables separate from the REST implementation.

## Documentation

| Document | Use |
| --- | --- |
| [Architecture](docs/architecture.md) | HTTP API request flow and authorization boundary |
| [Full Runbook](docs/cognito-auth-flow-https-runbook.md) | CLI implementation guide from AWS setup through protected route validation |
| [REST Version](../REST/README.md) | Companion REST API implementation |
| [Shared Lambda Code](../shared/lambda-code/) | Jedi and Sith Lambda handlers |
| [Secret Hash Helper](../shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper |

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

Use the [HTTPS runbook](docs/cognito-auth-flow-https-runbook.md) to build:

* Cognito user pool and app client
* Chewbacca test user with software token MFA
* Jedi Python Lambda
* Sith Node.js Lambda
* HTTP API routes
* HTTP API JWT authorizer
* End-to-end protected route tests

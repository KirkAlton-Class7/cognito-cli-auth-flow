# Chewbacca Cognito Auth Flow - REST Version

REST API implementation of the Chewbacca Cognito CLI auth-flow lab.<br>
View the HTTPS version [here](../HTTPS/README.md) if you prefer that implementation.<br><br>

This version uses API Gateway **REST API** resources and methods with a native Cognito User Pool authorizer. Build the infrastructure in the AWS Console, then use the CLI for the Cognito challenge flow, token export, and protected route tests.

> [!IMPORTANT]
> This folder documents the REST API implementation. REST APIs require an explicit deployment after method or authorizer changes.

## Documentation

| Document | Use |
| --- | --- |
| [Architecture](docs/architecture.md) | REST API request flow and authorization boundary |
| [Full Runbook](docs/cognito-auth-flow-rest-runbook.md) | Console infrastructure guide with CLI authentication and protected route validation |
| [HTTPS Version](../HTTPS/README.md) | Companion HTTP API implementation |
| [Shared Lambda Code](../shared/lambda-code/) | Jedi and Sith Lambda handlers |
| [Secret Hash Helper](../shared/scripts/secret_hash.py) | Cognito `SECRET_HASH` helper |

## Architecture Summary

```text
Chewbacca CLI
  -> Cognito USER_AUTH
  -> SELECT_CHALLENGE
  -> SOFTWARE_TOKEN_MFA
  -> ID token
  -> REST API Cognito User Pool authorizer
  -> Jedi/Sith Lambda
```

## Get Started

Use the [REST runbook](docs/cognito-auth-flow-rest-runbook.md) to build the infrastructure in the AWS Console and validate the authentication flow from the CLI:

* Cognito user pool and app client
* Chewbacca test user with software token MFA
* Jedi Python Lambda
* Sith Node.js Lambda
* REST API resources and GET methods
* REST API Cognito User Pool authorizer
* End-to-end protected route tests

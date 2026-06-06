# Cognito Auth Flow REST Lab

Hands-on lab for building and validating the REST implementation of the Cognito auth flow. This lab keeps the deeper explanation, visual checkpoints, and practice-oriented flow separate from the lean runbooks.

This lab isolates the authentication mechanics so you can see how Cognito behaves before putting the pattern inside a larger application. You will build a REST API protected by a Cognito User Pool authorizer, create a Chewbacca test user, enroll software-token MFA, use token helper scripts, and validate protected Jedi/Sith Lambda routes.

## Authentication and Authorization Flow

```text
User initiates authentication with Amazon Cognito
        ↓
Cognito validates credentials and required MFA challenges
        ↓
Cognito issues JWT tokens
        ↓
Client sends an API request with an access token
        ↓
API Gateway validates the JWT signature, claims, and required scope
        ↓
Authorized requests are routed to the appropriate Lambda function
        ↓
Unauthorized requests are rejected by API Gateway
        ↓
CloudWatch logs and metrics provide visibility into request processing
```

## Choose A Lab Path

| Document | Use |
| --- | --- |
| [CLI Lab With Environment File](lab-docs/LAB-CLI.md) | Build most resources with AWS CLI commands, then validate the full Cognito auth flow and protected REST routes. |
| [Console Lab With Environment File](lab-docs/LAB-CONSOLE.md) | Build most resources through the AWS Console while recording planned values, resource outputs, packaging commands, authentication, and validation in `.env`. |
| [REST Runbook - CLI](../../docs/RUNBOOK-CLI.md) | Use the action-focused CLI runbook after you understand the flow. |
| [REST Runbook - Console](../../docs/RUNBOOK-CONSOLE.md) | Use the action-focused Console runbook after you understand the flow. |
| [REST Lab Teardown](lab-docs/TEARDOWN_REST.md) | Remove only the base REST auth-flow resources built in this lab. |
| [REST README](../../README.md) | Return to the REST overview. |

## What You Build

- Chewbacca test user
- Cognito User Pool
- app clients for login page, SECRET_HASH, and token helper scripts
- USER_AUTH / SELECT_CHALLENGE
- PASSWORD
- SOFTWARE_TOKEN_MFA
- access token with aws.cognito.signin.user.admin scope
- API Gateway REST API Cognito authorizer
- protected /prod/jedi and /prod/sith Lambda routes
- CloudWatch Logs

The API routes are intentionally small so each authorization boundary is easy to inspect:

| Route | Runtime | Purpose |
| --- | --- | --- |
| `/prod/jedi` | Python | Validates the Python Lambda route after REST authorization succeeds |
| `/prod/sith` | Node.js | Validates the Node.js Lambda route after REST authorization succeeds |

## What You Practice

* Creating REST API resources, methods, Lambda proxy integrations, deployments, and stages.
* Creating Cognito user pools, app clients, users, MFA settings, and login-page styling.
* Walking the Cognito challenge flow with `SECRET_HASH`, `USER_AUTH`, `SELECT_CHALLENGE`, `PASSWORD`, and `SOFTWARE_TOKEN_MFA`.
* Understanding when to use the access token instead of the ID token for scoped REST API methods.
* Using token helper scripts after the manual authentication flow makes sense.
* Validating authorization failures, successful protected route calls, and CloudWatch evidence.

## Practice Sequence

Run the auth flow more than one way on purpose:

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
> Do the manual CLI pass first. Copying the `Session` value from `SELECT_CHALLENGE` into the password command, then copying the new `Session` into the MFA command, is the part that makes Cognito's challenge flow click. The export-based pass is included after that so you can repeat the lab quickly.

## Lab Assets

| Path | Purpose |
| --- | --- |
| [lab-docs/LAB-CLI.md](lab-docs/LAB-CLI.md) | CLI-first guided deployment lab. |
| [lab-docs/LAB-CONSOLE.md](lab-docs/LAB-CONSOLE.md) | Console-first guided deployment lab using `env.example` copied to `.env` for planned values and resource outputs. |
| [env.example](env.example) | Dotenv template to copy and rename to `.env` before starting the lab. |
| [lab-docs/TEARDOWN_REST.md](lab-docs/TEARDOWN_REST.md) | Lab-specific teardown for resources created by this lab. |
| [../../docs/RUNBOOK-CLI.md](../../docs/RUNBOOK-CLI.md) | Lean CLI reference for the same REST flow. |
| [../../docs/RUNBOOK-CONSOLE.md](../../docs/RUNBOOK-CONSOLE.md) | Lean Console reference for the same REST flow. |
| [../../../shared/lambda-code/](../../../shared/lambda-code/) | Shared Jedi and Sith Lambda source. |
| [../../../shared/scripts/](../../../shared/scripts/) | Secret hash and token helper scripts. |
| [/assets/images/](../../../assets/images/) | Screenshots used throughout the lab docs. |

## Recommended Order

Start with the Console lab if you want to see each AWS service boundary and capture the visual workflow. Start with the CLI lab if you want repeatable commands and a faster rebuild workflow.

After the base REST auth flow works, continue with the token detector add-on:

* [Token Detector](../../../deploy-token-detector/README.md)
* [Token Detector Lab](../../../deploy-token-detector/labs/token-detector/LAB-README.md)

## Concept Overview

This lab covers these core areas:

- Amazon Cognito user authentication
- Software-token MFA with authenticator apps
- Cognito app clients with and without client secrets
- `SECRET_HASH` validation
- Cognito challenge flow sequencing
- Access tokens, ID tokens, and refresh tokens
- REST API Cognito User Pool authorizers
- Authorization scopes for protected API routes
- Lambda proxy integration routing
- CloudWatch log validation

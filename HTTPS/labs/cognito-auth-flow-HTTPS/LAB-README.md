# Cognito Auth Flow HTTPS Lab

Hands-on lab for building and validating the HTTPS/HTTP API version of the Cognito auth flow. This lab keeps the deeper explanation and practice-oriented flow separate from the lean runbooks.

This lab walks through an HTTP API protected by a Cognito JWT authorizer, a themed test user, software token MFA, token helper scripts, and protected Jedi/Sith Lambda routes.

## Choose A Lab Path

| Document | Use |
| --- | --- |
| [CLI Lab](lab-docs/LAB-CLI.md) | Build most resources with AWS CLI commands, then validate the full Cognito auth flow and protected HTTP API routes. |
| [Console Lab](lab-docs/LAB-CONSOLE.md) | Build most resources through the AWS Console, using CLI commands for packaging, exports, authentication, and validation. |
| [HTTPS Runbook - CLI](../../docs/RUNBOOK-CLI.md) | Use the action-focused CLI runbook after you understand the flow. |
| [HTTPS Runbook - Console](../../docs/RUNBOOK-CONSOLE.md) | Use the action-focused Console runbook after you understand the flow. |
| [HTTPS Teardown](../../docs/TEARDOWN_HTTPS.md) | Remove only the base HTTPS auth-flow resources. |
| [HTTPS README](../../README.md) | Return to the HTTPS overview. |

## What You Build

```text
Themed test user
  -> Cognito User Pool
  -> app clients for token helper scripts
  -> USER_AUTH / SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> access token
  -> API Gateway HTTP API JWT authorizer
  -> protected /prod/jedi and /prod/sith Lambda routes
```

## What You Practice

* Creating HTTP API routes, integrations, stages, and JWT authorizers.
* Creating Cognito user pools, app clients, users, and software token MFA settings.
* Walking the Cognito challenge flow with `SECRET_HASH`, `USER_AUTH`, `SELECT_CHALLENGE`, `PASSWORD`, and `SOFTWARE_TOKEN_MFA`.
* Using access tokens with HTTP API JWT authorizers.
* Using token helper scripts after the manual authentication flow makes sense.
* Validating authorization failures, successful protected route calls, and CloudWatch evidence.

## Lab Assets

| Path | Purpose |
| --- | --- |
| [lab-docs/LAB-CLI.md](lab-docs/LAB-CLI.md) | CLI-first guided lab. |
| [lab-docs/LAB-CONSOLE.md](lab-docs/LAB-CONSOLE.md) | Console-first guided lab. |
| [../../docs/RUNBOOK-CLI.md](../../docs/RUNBOOK-CLI.md) | Lean CLI reference for the same HTTPS flow. |
| [../../docs/RUNBOOK-CONSOLE.md](../../docs/RUNBOOK-CONSOLE.md) | Lean Console reference for the same HTTPS flow. |
| [../../../shared/lambda-code/](../../../shared/lambda-code/) | Shared Jedi and Sith Lambda source. |
| [../../../shared/scripts/](../../../shared/scripts/) | Secret hash and token helper scripts. |

## Recommended Order

Start with the Console lab if you want to see each AWS service boundary. Start with the CLI lab if you want repeatable commands and a faster rebuild path.

After the base HTTPS auth flow works, continue with the token detector add-on:

* [Token Detector](../../../deploy-token-detector/README.md)
* [Token Detector Lab](../../../deploy-token-detector/labs/token-detector/LAB-README.md)

## Final Check

You are ready to leave this lab when you can explain this flow without looking:

```text
SECRET_HASH proves the app client secret
USER_AUTH starts negotiation
SELECT_CHALLENGE lets the client choose PASSWORD
PASSWORD validates the primary factor
SOFTWARE_TOKEN_MFA validates the second factor
Cognito issues JWT tokens
HTTP API JWT authorizer validates the access token
Lambda only runs after authorization succeeds
CloudWatch proves what actually happened
```

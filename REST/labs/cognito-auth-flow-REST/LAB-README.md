# Cognito Auth Flow REST Lab

Hands-on lab for building and validating the REST version of the Cognito auth flow. This lab keeps the deeper explanation, visual checkpoints, and practice-oriented flow separate from the lean runbooks.

This lab walks through a REST API protected by a Cognito User Pool authorizer, a Chewbacca test user, software token MFA, token helper scripts, and protected Jedi/Sith Lambda routes.

## Choose A Lab Path

| Document | Use |
| --- | --- |
| [CLI Lab](lab-docs/LAB-CLI.md) | Build most resources with AWS CLI commands, then validate the full Cognito auth flow and protected REST routes. |
| [Console Lab](lab-docs/LAB-CONSOLE.md) | Build most resources through the AWS Console, using CLI commands for packaging, exports, authentication, and validation. |
| [REST Runbook - CLI](../../docs/RUNBOOK-CLI.md) | Use the action-focused CLI runbook after you understand the flow. |
| [REST Runbook - Console](../../docs/RUNBOOK-CONSOLE.md) | Use the action-focused Console runbook after you understand the flow. |
| [REST Teardown](../../docs/TEARDOWN_REST.md) | Remove only the base REST auth-flow resources. |
| [REST README](../../README.md) | Return to the REST overview. |

## What You Build

```text
Chewbacca test user
  -> Cognito User Pool
  -> app clients for login page and token helper scripts
  -> USER_AUTH / SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> access token with aws.cognito.signin.user.admin scope
  -> API Gateway REST API Cognito authorizer
  -> protected /prod/jedi and /prod/sith Lambda routes
```

## What You Practice

* Creating REST API resources, methods, Lambda proxy integrations, deployments, and stages.
* Creating Cognito user pools, app clients, users, MFA settings, and login-page styling.
* Walking the Cognito challenge flow with `SECRET_HASH`, `USER_AUTH`, `SELECT_CHALLENGE`, `PASSWORD`, and `SOFTWARE_TOKEN_MFA`.
* Understanding when to use the access token instead of the ID token for scoped REST API methods.
* Using token helper scripts after the manual authentication flow makes sense.
* Validating authorization failures, successful protected route calls, and CloudWatch evidence.

## Lab Assets

| Path | Purpose |
| --- | --- |
| [lab-docs/LAB-CLI.md](lab-docs/LAB-CLI.md) | CLI-first guided lab. |
| [lab-docs/LAB-CONSOLE.md](lab-docs/LAB-CONSOLE.md) | Console-first guided lab. |
| [../../docs/RUNBOOK-CLI.md](../../docs/RUNBOOK-CLI.md) | Lean CLI reference for the same REST flow. |
| [../../docs/RUNBOOK-CONSOLE.md](../../docs/RUNBOOK-CONSOLE.md) | Lean Console reference for the same REST flow. |
| [../../../shared/lambda-code/](../../../shared/lambda-code/) | Shared Jedi and Sith Lambda source. |
| [../../../shared/scripts/](../../../shared/scripts/) | Secret hash and token helper scripts. |
| [/assets/temp/](/assets/temp/) | Screenshots used throughout the lab docs. |

## Recommended Order

Start with the Console lab if you want to see each AWS service boundary and capture the visual workflow. Start with the CLI lab if you want repeatable commands and a faster rebuild path.

After the base REST auth flow works, continue with the token detector add-on:

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
REST API Cognito authorizer validates the access token for scoped methods
Lambda only runs after authorization succeeds
CloudWatch proves what actually happened
```

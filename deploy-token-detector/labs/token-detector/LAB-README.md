# Unused Token Detector Lab

Hands-on lab for extending the Cognito auth flow with token-use telemetry and unused-token detection.<br>
Use the ready code path [here](../../README.md) if you want the concise runbook and packaged code.<br><br>

This lab is intentionally editing-first. You can edit directly in AWS, but the recommended flow is to copy starter code into `sandbox/`, edit locally, then add the edited code in AWS and deploy. The `quick-deployment/` files are finished references for when you want to move quickly after the manual path makes sense.

> [!IMPORTANT]
> Do not pre-fill `sandbox/` with quick-deployment files. The sandbox is the student workspace for copying starter files from `shared/` and making the lab edits.

## Documentation

| Document | Use |
| --- | --- |
| [Full Lab](lab-docs/deploy-token-detector-lab.md) | Guided manual editing path with AWS console and CLI validation |
| [REST Teardown](lab-docs/TEARDOWN_REST.md) | Remove REST resources plus detector resources |
| [HTTPS Teardown](lab-docs/TEARDOWN_HTTPS.md) | Remove HTTPS resources plus detector resources |
| [Token Detector Runbook](../../README.md) | Concise path with finished code |

## Lab Assets

| Path | Purpose |
| --- | --- |
| `sandbox/` | Empty workspace for local student edits |
| `sandbox/scripts/` | Local helper-script copies created during the lab |
| `sandbox/lambda-code/` | Local Lambda-code copies created during the lab |
| [quick-deployment/get_token.py](quick-deployment/get_token.py) | Finished token helper |
| [quick-deployment/jedi_python_token_tracker.py](quick-deployment/jedi_python_token_tracker.py) | Finished Jedi Python route handler |
| [quick-deployment/sith_node_token_tracker.js](quick-deployment/sith_node_token_tracker.js) | Finished Sith Node.js route handler |
| [quick-deployment/unused_token_detector.py](quick-deployment/unused_token_detector.py) | Finished unused-token detector Lambda |

## Learning Flow

```text
Copy starter code from shared/
  -> edit in sandbox/
  -> add edited code in AWS
  -> generate a token
  -> mark it used through /jedi or /sith
  -> scan for unused tokens
  -> create alerting
```

## What You Practice

* Copying and modifying `shared/scripts/flavor_get_token.py`
* Preserving the existing Jedi and Sith route logic
* Adding DynamoDB token records after authentication
* Passing `x-token-id` through curl examples
* Updating both Python and Node.js route Lambdas
* Creating a detector Lambda for stale unused tokens
* Building CloudWatch and SNS alerting from detector logs

## Get Started

Start with the [full lab](lab-docs/deploy-token-detector-lab.md). Build the base auth flow first with either:

* [REST Version](../../../REST/README.md)
* [HTTPS Version](../../../HTTPS/README.md)

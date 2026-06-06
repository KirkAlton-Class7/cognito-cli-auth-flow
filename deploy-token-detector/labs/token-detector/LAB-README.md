# Unused Token Detector Lab

Hands-on lab for extending the Cognito auth flow with token-use telemetry and unused-token detection.<br>
Use the ready code path [here](../../README.md) if you want the concise runbook and packaged code.<br><br>

This lab is intentionally editing-first. You can edit directly in AWS, but the recommended flow is to copy starter code into `sandbox/`, edit locally, then add the edited code in AWS and deploy. The `quick-deployment/` files are finished references for comparison after the manual path makes sense. Use the runbook for the concise quick deployment flow.

The add-on starts after a base REST or HTTPS auth flow exists. Cognito still issues the token, API Gateway still validates it, and Lambda still runs only after authorization succeeds. This lab adds the telemetry layer that lets you ask a new question: which issued tokens were never used against the protected routes?

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
| [quick-deployment/get_token.py](quick-deployment/get_token.py) | Finished token helper reference |
| [quick-deployment/jedi_python_token_tracker.py](quick-deployment/jedi_python_token_tracker.py) | Finished Jedi Python route handler reference |
| [quick-deployment/sith_node_token_tracker.js](quick-deployment/sith_node_token_tracker.js) | Finished Sith Node.js route handler reference |
| [quick-deployment/unused_token_detector.py](quick-deployment/unused_token_detector.py) | Finished unused-token detector Lambda reference |

## Learning Flow

- Base Cognito auth flow works
- copy starter code from shared/
- edit in sandbox/
- add edited code in AWS
- generate a token
- write a token record to DynamoDB
- pass x-token-id through /jedi or /sith
- mark the token used
- scan for unused tokens
- create alerting from detector logs

## What You Practice

* Copying and modifying `shared/scripts/flavor_get_token.py`.
* Preserving the existing Jedi and Sith route logic while adding token telemetry.
* Adding DynamoDB token records after authentication.
* Passing `x-token-id` through curl examples and Lambda events.
* Updating both Python and Node.js route Lambdas.
* Creating a detector Lambda for stale unused tokens.
* Building CloudWatch and SNS alerting from detector logs.
* Using CloudWatch evidence to prove whether a token was issued, used, or left unused.

## Practice Sequence

Work through the edits manually before using the runbook for quick deployment:

```text
Manual edit pass:
  copy starter files into sandbox/
  add imports, configuration, and DynamoDB calls
  keep route behavior intact
  deploy edited code in AWS

Validation pass:
  run the token helper script
  call a protected Jedi or Sith route
  confirm DynamoDB records issued and used tokens
  run the unused-token detector

Quick deployment pass:
  compare your sandbox edits to quick-deployment files
  use the runbook when you want a faster rebuild
```

## Get Started

Start with the [full lab](lab-docs/deploy-token-detector-lab.md). Build the base auth flow first with either:

* [REST Version](../../../REST/README.md)
* [HTTPS Version](../../../HTTPS/README.md)

## Validation Checklist

Use this checklist before you consider the token detector lab complete:

- [ ] Start from a working REST or HTTPS Cognito auth flow.
- [ ] Copy `env.example` to `.env`, update planned values, and reload it before dependent commands.
- [ ] Create the DynamoDB token table with `token_id` as the partition key.
- [ ] Add the DynamoDB access policy to the Lambda role used by the route and detector functions.
- [ ] Copy starter helper code into `sandbox/scripts/` and add the `uuid` import.
- [ ] Add a DynamoDB token record after a token is issued, with `used` set to `False`.
- [ ] Preserve the routing logic from the original token helper script.
- [ ] Print curl examples that include the generated `x-token-id` header.
- [ ] Copy starter Jedi and Sith route code into `sandbox/lambda-code/`.
- [ ] Update the Python route Lambda to read `x-token-id` and mark matching records used.
- [ ] Update the Node.js route Lambda to read `x-token-id` and mark matching records used.
- [ ] Preserve the original Jedi and Sith route response behavior after adding token telemetry.
- [ ] Create or deploy `unused_token_detector.py` with the token table environment variable.
- [ ] Run `get_token.py` and confirm a new DynamoDB item is created.
- [ ] Call a protected Jedi or Sith route with `x-token-id` and confirm DynamoDB marks the token used.
- [ ] Generate a token and intentionally do not use it.
- [ ] Invoke the detector after the unused threshold and confirm `ALERT: Token unused` appears in CloudWatch Logs.
- [ ] Create the EventBridge Scheduler rule for recurring detector scans.
- [ ] Create the SNS topic, CloudWatch metric filter, and CloudWatch alarm for unused-token alerts.
- [ ] Run the lab teardown from the matching lab teardown file when you are ready to remove the detector resources.

## Concept Takeaways

- Cognito can issue valid tokens that are never used against protected APIs; token issuance and token usage are different events.
- DynamoDB gives each issued token a durable tracking record keyed by `token_id`.
- The `x-token-id` header connects an API call back to the token-helper record without changing Cognito itself.
- The Jedi and Sith route Lambdas should keep their original route behavior while adding token-use telemetry.
- The detector Lambda turns stored token metadata into an operational signal by finding old records where `used` is still `False`.
- CloudWatch metric filters convert detector log lines into metrics, and alarms turn those metrics into notifications.
- EventBridge Scheduler makes detection recurring instead of manual.
- This pattern practices security observability: proving not just who authenticated, but whether the issued credential was used.

## Final Check

You are ready to leave this token detector lab when you can explain the full path without looking:

```text
Cognito issues JWT tokens
get_token.py records issued token metadata in DynamoDB
Protected routes receive x-token-id after API Gateway authorization succeeds
Jedi and Sith Lambdas mark matching token records as used
unused_token_detector.py scans for old unused token records
CloudWatch metric filters turn detector logs into alert signals
SNS delivers the unused-token notification path
```

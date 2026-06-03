# Chewbacca Cognito Token Detector

Token-use tracking extension for the Chewbacca Cognito CLI auth-flow lab.<br>
Use the hands-on lab [here](../LABS/jedi-token-detector/README.md) if you want to practice making the code changes step by step.<br><br>

This folder contains the ready code path for recording issued tokens, marking tokens used when either protected route is called, and scanning for stale unused tokens.

Start with one of the base API implementations:

* [HTTPS Version](../HTTPS/README.md)
* [REST Version](../REST/README.md)

> [!IMPORTANT]
> Keep the project name aligned with the API version you are extending. HTTPS commonly uses `chewbacca-auth-http`; REST commonly uses `chewbacca-auth-rest`.

## Documentation

| Document | Use |
| --- | --- |
| [Full Runbook](docs/deploy-token-detector-runbook.md) | Add token tracking, route updates, detector Lambda, schedule, and alerting |
| [REST Teardown](docs/TEARDOWN_REST.md) | Remove REST lab resources plus token-detector resources |
| [HTTPS Teardown](docs/TEARDOWN_HTTPS.md) | Remove HTTPS lab resources plus token-detector resources |
| [Lab Version](../LABS/jedi-token-detector/README.md) | Guided editing path for learning the same changes |

## Source Material

| Path | Purpose |
| --- | --- |
| [scripts/get_token.py](scripts/get_token.py) | Token helper that writes a DynamoDB token record and prints Jedi/Sith curl examples with `x-token-id` |
| [lambda-code/jedi_python_token_tracker.py](lambda-code/jedi_python_token_tracker.py) | Jedi Python route handler that marks a token used |
| [lambda-code/sith_node_token_tracker.js](lambda-code/sith_node_token_tracker.js) | Sith Node.js route handler that marks a token used |
| [lambda-code/unused_token_detector.py](lambda-code/unused_token_detector.py) | Detector Lambda that logs unused token alerts |

## Architecture Summary

```text
Cognito token helper
  -> DynamoDB token record
  -> API Gateway /prod/jedi or /prod/sith
  -> route Lambda marks token used
  -> detector Lambda scans for stale unused tokens
  -> CloudWatch metric filter
  -> SNS alert
```

## Get Started

Use the [token detector runbook](docs/deploy-token-detector-runbook.md) after building either the REST or HTTPS base auth flow.

The flow adds:

* DynamoDB token holocron table
* Updated Jedi and Sith route Lambda code
* Token helper that records issued tokens
* Unused-token detector Lambda
* EventBridge schedule
* CloudWatch metric filter and SNS alarm

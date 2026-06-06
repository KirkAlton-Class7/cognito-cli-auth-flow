# Cognito Token Detector

Token-use tracking extension for the Cognito auth-flow lab.<br>
Use the hands-on lab [here](labs/token-detector/LAB-README.md) if you want to practice making the code changes step by step.<br><br>

This folder contains ready-to-use code for recording issued tokens, marking tokens used when either protected route is called, and scanning for stale unused tokens.

Start with one of the base API implementations:

* [HTTPS Deployment](../HTTPS/README.md)
* [REST Deployment](../REST/README.md)

> [!IMPORTANT]
> Keep the project name aligned with the API deployment you are extending. HTTPS commonly uses `chewbacca-auth-http`; REST commonly uses `chewbacca-auth-rest`.

## Documentation

| Document | Use |
| --- | --- |
| [Full Runbook](docs/deploy-token-detector-runbook.md) | Add token tracking, route updates, detector Lambda, schedule, and alerting |
| [REST Teardown](docs/TEARDOWN_REST.md) | Remove REST resources plus token-detector resources |
| [HTTPS Teardown](docs/TEARDOWN_HTTPS.md) | Remove HTTPS resources plus token-detector resources |
| [Lab](labs/token-detector/LAB-README.md) | Guided editing workflow for learning the same changes |

## Source Material

| Path | Purpose |
| --- | --- |
| [scripts/get_token.py](scripts/get_token.py) | Token helper that writes a DynamoDB token record and prints Jedi/Sith curl examples with `x-token-id` |
| [lambda-code/jedi_python_token_tracker.py](lambda-code/jedi_python_token_tracker.py) | Jedi Python route handler that marks a token used |
| [lambda-code/sith_node_token_tracker.js](lambda-code/sith_node_token_tracker.js) | Sith Node.js route handler that marks a token used |
| [lambda-code/unused_token_detector.py](lambda-code/unused_token_detector.py) | Detector Lambda that logs unused token alerts |

## Deployment Components

- DynamoDB token holocron table
- Updated Jedi and Sith route Lambda code
- Token helper that records issued tokens
- API Gateway `/prod/jedi` and `/prod/sith` routes with `x-token-id`
- Unused-token detector Lambda
- EventBridge schedule
- CloudWatch metric filter and SNS alarm

## Detection Flow

- The token helper writes a token record when Cognito issues tokens.
- Protected API calls send the token ID with the request.
- Route Lambda code marks the matching token record used.
- The detector Lambda scans for stale unused token records.
- CloudWatch and SNS surface unused-token alerts.

## Get Started

Use the [token detector runbook](docs/deploy-token-detector-runbook.md) after building either the REST or HTTPS base auth flow.

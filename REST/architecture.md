# Cognito Auth Flow - REST Architecture

The REST version uses API Gateway REST API resources and methods with a native Cognito User Pool authorizer. Cognito owns the user authentication flow. API Gateway validates the token before invoking Lambda.

- Chewbacca CLI
- Cognito initiate-auth USER_AUTH
- SELECT_CHALLENGE
- PASSWORD
- SOFTWARE_TOKEN_MFA
- access token with aws.cognito.signin.user.admin scope
- API Gateway REST API Cognito User Pool authorizer
- /prod/jedi or /prod/sith
- Lambda
- CloudWatch Logs

## Route Map

| Route | Runtime | Integration | Authorization |
| --- | --- | --- | --- |
| `GET /prod/jedi` | Python | Lambda proxy integration | REST API Cognito User Pool authorizer |
| `GET /prod/sith` | Node.js | Lambda proxy integration | REST API Cognito User Pool authorizer |

## Boundary Notes

* Cognito issues the tokens.
* REST API validates the access token with a Cognito User Pool authorizer and method authorization scope attached to each protected method.
* Lambda is not invoked when the token is missing or invalid.
* REST API changes require a new deployment before the `prod` stage reflects them.
* No custom authorizer Lambda is required for this Cognito-only lab.

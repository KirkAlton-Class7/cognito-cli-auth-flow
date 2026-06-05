# Cognito Auth Flow - HTTPS Architecture

The HTTPS version uses API Gateway HTTP API with a built-in JWT authorizer. Cognito owns the user authentication flow. API Gateway validates the token before Lambda runs.

```text
Chewbacca CLI
  -> Cognito initiate-auth USER_AUTH
  -> SELECT_CHALLENGE
  -> PASSWORD
  -> SOFTWARE_TOKEN_MFA
  -> Access token
  -> API Gateway HTTP API JWT authorizer
  -> /prod/jedi or /prod/sith
  -> Lambda
  -> CloudWatch Logs
```

## Route Map

| Route | Runtime | Integration | Authorization |
| --- | --- | --- | --- |
| `GET /prod/jedi` | Python | Lambda proxy integration | HTTP API JWT authorizer |
| `GET /prod/sith` | Node.js | Lambda proxy integration | HTTP API JWT authorizer |

## Boundary Notes

* Cognito issues the tokens.
* HTTP API validates issuer and audience through the JWT authorizer.
* Lambda is not invoked when the token is missing or invalid.
* The same `ACCESS_TOKEN` generated from the CLI auth flow is used in `Authorization: Bearer $ACCESS_TOKEN`.
* No custom authorizer Lambda is required.

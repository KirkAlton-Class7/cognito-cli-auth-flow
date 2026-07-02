resource "aws_api_gateway_rest_api" "chewbacca_auth_rest_api" {
  name = "${local.name_prefix}-rest-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "trigger_deployment" {
  rest_api_id = aws_api_gateway_rest_api.chewbacca_auth_rest_api.id

  triggers = {
  redeployment = sha1(jsonencode([
    # To force a redeployment without changing these keys/values,
    # use the -replace option with terraform plan or terraform apply.
    aws_api_gateway_resource.login,
    aws_api_gateway_method.post,
    aws_api_gateway_integration.lambda,
  ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.example.id
  rest_api_id   = aws_api_gateway_rest_api.chewbacca_auth_rest_api.id
  stage_name    = "example"
}




# triggers = {
#   # Resources
#   resources = sha1(
#     jsonencode(local.deployment_trigger_resources)
#   )

#   # Authorizers
#   authorizers = sha1(
#     jsonencode(local.deployment_trigger_authorizers)
#   )

#   # Gateway Responses
#   gateway_responses = sha1(
#     jsonencode(local.deployment_trigger_gateway_responses)
#   )

#   # Models
#   models = sha1(
#     jsonencode(local.deployment_trigger_models)
#   )

#   # Resource Policy
#   resource_policy = sha1(
#     jsonencode(
#       aws_api_gateway_rest_api_policy.this.policy
#     )
#   )
# }

# ---------------

resource "aws_api_gateway_rest_api" "example" {
  name = "example"
}

resource "aws_api_gateway_resource" "example" {
  parent_id   = aws_api_gateway_rest_api.example.root_resource_id
  path_part   = "example"
  rest_api_id = aws_api_gateway_rest_api.example.id
}

resource "aws_api_gateway_method" "example" {
  authorization = "NONE"
  http_method   = "GET"
  resource_id   = aws_api_gateway_resource.example.id
  rest_api_id   = aws_api_gateway_rest_api.example.id
}

resource "aws_api_gateway_integration" "example" {
  http_method = aws_api_gateway_method.example.http_method
  resource_id = aws_api_gateway_resource.example.id
  rest_api_id = aws_api_gateway_rest_api.example.id
  type        = "MOCK"
}

resource "aws_api_gateway_deployment" "example" {
  rest_api_id = aws_api_gateway_rest_api.example.id

  triggers = {
    # NOTE: The configuration below will satisfy ordering considerations,
    #       but not pick up all future REST API changes. More advanced patterns
    #       are possible, such as using the filesha1() function against the
    #       Terraform configuration file(s) or removing the .id references to
    #       calculate a hash against whole resources. Be aware that using whole
    #       resources will show a difference after the initial implementation.
    #       It will stabilize to only change when resources change afterwards.
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.example.id,
      aws_api_gateway_method.example.id,
      aws_api_gateway_integration.example.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "example" {
  deployment_id = aws_api_gateway_deployment.example.id
  rest_api_id   = aws_api_gateway_rest_api.example.id
  stage_name    = "example"
}
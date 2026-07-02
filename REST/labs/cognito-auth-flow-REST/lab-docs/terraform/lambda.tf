# -------------------------------------------------------------------------------
# Lambda Function - Jedi Python
# -------------------------------------------------------------------------------
resource "aws_lambda_function" "jedi_python" {
  filename         = data.archive_file.jedi_python.output_path
  source_code_hash = data.archive_file.jedi_python.output_base64sha256

  function_name = "${local.name_prefix}-jedi-python"
  role          = aws_iam_role.jedi_python_role.arn

  handler = "lambda.handler"
  runtime = "python3.14"
}

# Zip Archive - Jedi Python
data "archive_file" "jedi_python" {
  type        = "zip"
  source_file = "${path.module}/lambda-code/jedi_python.py"
  output_path = "${path.module}/lambda-code/jedi_python.zip"
}

# -------------------------------------------------------------------------------
# Lambda Function - Sith Node
# -------------------------------------------------------------------------------
resource "aws_lambda_function" "sith_node" {
  filename         = data.archive_file.sith_node.output_path
  source_code_hash = data.archive_file.sith_node.output_base64sha256

  function_name = "${local.name_prefix}-sith-node"
  role          = aws_iam_role.sith_node_role.arn

  handler = "index.handler"
  runtime = "nodejs24.x"
}

# Zip Archive - Sith Node
data "archive_file" "sith_node" {
  type        = "zip"
  source_file = "${path.module}/lambda-code/sith_node.js"
  output_path = "${path.module}/lambda-code/sith_node.zip"
}

# -------------------------------------------------------------------------------
# Lambda Function - Unused Token Detector
# -------------------------------------------------------------------------------
resource "aws_lambda_function" "unused_token_detector" {
  filename         = data.archive_file.unused_token_detector.output_path
  source_code_hash = data.archive_file.unused_token_detector.output_base64sha256

  function_name = "${local.name_prefix}-unused-token-detector"
  role          = aws_iam_role.unused_token_detector_role.arn

  handler = "lambda.handler"
  runtime = "python3.14"
}

# Zip Archive - Unused Token Detector
data "archive_file" "unused_token_detector" {
  type        = "zip"
  source_file = "${path.module}/lambda-code/unused_token_detector.py"
  output_path = "${path.module}/lambda-code/unused_token_detector.zip"
}











# Refactor

# Jae's Code
# resource "aws_lambda_function" "jae_lambda" {
#   for_each = var.function_code_config

#   filename         = data.archive_file.example[each.key].output_path
#   function_name    = each.value.function_name
#   role             = aws_iam_role.lambda_execution_role.arn
#   handler          = "${each.value.file_name}.${each.value.handler}"
#   code_sha256      = data.archive_file.example[each.key].output_base64sha256
#   architectures    = each.value.architecture
#   runtime          = each.value.runtime
#   description      = each.value.description

#   environment {
#     # for environmental variables, this lookup function uses the locals as a dictionary
#     # through which the env_value portion of the specific var.function_code_config
#     # if nothing is found, it will return the default 'v' (the value itself)
#     variables = {
#       for k, v in each.value.env_value : k => lookup(local.env_variables, v, v)
#     }
#   }

#   tags = {
#     Name        = each.value.function_name
#     Environment = "Test"
#     Managed_by  = "Terraform"
#   }
# }





# resource "aws_api_gateway_deployment" "api_rest" {
#   triggers = {
#     # Forces redeployment when this value changes (e.g., on API changes)
#     redeployment = sha1(jsonencode([1]))
#   }

#   lifecycle {
#     create_before_destroy = true
#   }
# }

# resource "aws_api_gateway_stage" "api_rest" {
#   deployment_id = aws_api_gateway_deployment.api_rest.id
#   rest_api_id   = aws_api_gateway_rest_api.api_rest.id
#   stage_name    = "prod"
# }

# resource "aws_lambda_permission" "lambda_permission" {
#   statement_id  = "AllowMyDemoAPIInvoke"
#   action        = "lambda:InvokeFunction"
#   function_name = "MyDemoFunction"
#   principal     = "apigateway.amazonaws.com"

#   # The /* part allows invocation from any stage, method, and resource path
#   # within API Gateway.
#   source_arn = "${aws_api_gateway_rest_api.MyDemoAPI.execution_arn}/*"
# }







# # Data sources to fetch dynamic AWS account/region/partition info
# data "aws_region" "current" {}
# data "aws_partition" "current" {}
# data "aws_caller_identity" "current" {}  # ← You were missing this one!

# resource "aws_lambda_permission" "lambda_permission" {
#   statement_id  = "AllowAPIGatewayInvoke"
#   action        = "lambda:InvokeFunction"
#   function_name = "MyDemoFunction"
#   principal     = "apigateway.amazonaws.com"

#   # Full ARN for the API Gateway endpoint
#   # /*/* grants access to any stage (*), any HTTP method (*), and any resource path (*)
#   source_arn = "arn:${data.aws_partition.current.partition}:execute-api:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.j_rest_api.id}/*/*"
# }
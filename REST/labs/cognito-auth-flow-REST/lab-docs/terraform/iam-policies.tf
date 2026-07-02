# -------------------------------------------------------------------------------
# DynamoDB Scan (scan/read/write)
# -------------------------------------------------------------------------------
# IAM Policy Object
resource "aws_iam_policy" "dynamo_db_lambda_scan" {
  name        = "dynamo-db-lambda-scan-${local.name_suffix}"
  description = "Allows DynamoDB scan and write operations on the Jedi token holocron table"
  policy      = data.aws_iam_policy_document.dynamo_db_lambda_scan.json
}

# IAM Policy Data
data "aws_iam_policy_document" "dynamo_db_lambda_scan" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Scan",
      "dynamodb:Query"
    ]
    resources = [
      "arn:aws:dynamodb${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/chewbacca-auth-rest-jedi-token-holocron"
    ]
  }
}

# -------------------------------------------------------------------------------
# Policy Document – Invoke Bedrock models
# -------------------------------------------------------------------------------
# IAM Policy Object
resource "aws_iam_policy" "invoke_bedrock" {
  name        = "invoke-bedrock-${local.name_suffix}"
  description = "Allows invoking Bedrock foundation models"
  policy      = data.aws_iam_policy_document.invoke_bedrock.json
}

# IAM Policy Data
data "aws_iam_policy_document" "invoke_bedrock" {
  statement {
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = ["*"]
  }
}


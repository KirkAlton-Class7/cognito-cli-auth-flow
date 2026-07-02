# -------------------------------------------------------------------------------
# IAM Role - Jedi Python
# -------------------------------------------------------------------------------
resource "aws_iam_role" "jedi_python_role" {
  name               = "jedi-python-role-${local.name_suffix}"
  assume_role_policy = data.aws_iam_policy_document.jedi_python_assume_role.json
  description        = "Role for Jedi Python Lambda"

  tags = {
    Name        = ""
    Component   = ""
    DataClass   = ""
    AccessLevel = ""
  }
}

# Trust Policy Data for Jedi Python Role
data "aws_iam_policy_document" "jedi_python_assume_role" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# IAM Policy Attachments
resource "aws_iam_role_policy_attachment" "jedi_python_attach_basic_execution_role" {
  role       = aws_iam_role.jedi_python_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -------------------------------------------------------------------------------
# IAM Role - Sith Node
# -------------------------------------------------------------------------------
resource "aws_iam_role" "sith_node_role" {
  name               = "sith-node-role-${local.name_suffix}"
  assume_role_policy = data.aws_iam_policy_document.sith_node_assume_role.json
  description        = "Role for Sith Node Lambda"

  tags = {
    Name        = ""
    Component   = ""
    DataClass   = ""
    AccessLevel = ""
  }
}

# Trust Policy Data for Sith Node Role
data "aws_iam_policy_document" "sith_node_assume_role" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# IAM Policy Attachments
resource "aws_iam_role_policy_attachment" "sith_node_attach_basic_execution_role" {
  role       = aws_iam_role.sith_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -------------------------------------------------------------------------------
# IAM Role - Unused Token Detector
# -------------------------------------------------------------------------------
resource "aws_iam_role" "unused_token_detector_role" {
  name               = "unused-token-detector-${local.name_suffix}"
  assume_role_policy = data.aws_iam_policy_document.unused_token_detector_assume_role.json
  description        = "Role for Unused Token Detector Lambda"

  tags = {
    Name        = ""
    Component   = ""
    DataClass   = ""
    AccessLevel = ""
  }
}

# Trust Policy Data for Sith Node Role
data "aws_iam_policy_document" "unused_token_detector_assume_role" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# IAM Policy Attachments
resource "aws_iam_role_policy_attachment" "unused_token_dectector_attach_basic_execution_role" {
  role       = aws_iam_role.unused_token_detector_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "attach_dynamo_db_lambda_scan" {
  role       = aws_iam_role.unused_token_detector_role.name
  policy_arn = aws_iam_policy.dynamo_db_lambda_scan.arn
}

resource "aws_iam_role_policy_attachment" "attach_invoke_bedrock" {
  role       = aws_iam_role.unused_token_detector_role.name
  policy_arn = aws_iam_policy.invoke_bedrock.arn
}

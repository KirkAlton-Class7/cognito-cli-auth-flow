# ================================================================
# BACKEND
# ================================================================
# Choose one backend platform and remove the others.

# ----------------------------------------------------------------
# Terraform Backend Configuration - Google (GCS)
# ----------------------------------------------------------------
# Documentation - GCS Backend
# https://www.terraform.io/language/settings/backends/gcs

terraform {
  backend "gcs" {
    bucket = "kirkdevsecops-terraform-state"
    prefix = "chewbacca-auth-rest-lab/dev"
  }
}

# ----------------------------------------------------------------
# Terraform Backend Configuration - AWS (S3)
# ----------------------------------------------------------------
# Documentation - S3 Backend
# https://developer.hashicorp.com/terraform/language/backend/s3

# terraform {
#   backend "s3" {
#     bucket = "kirkdevsecops-terraform-state"
#     key = "class7/terraform/dev/quick-vpc/terraform.tfstate"
#     region = "us-west-2"
#   }
# }
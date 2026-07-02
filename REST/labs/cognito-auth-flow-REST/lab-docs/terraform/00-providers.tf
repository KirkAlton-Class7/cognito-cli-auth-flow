# ================================================================
# TERRAFORM PROVIDERS
# ================================================================
# Remove blocks for providers that aren't used.

# ----------------------------------------------------------------
# Required Providers
# ----------------------------------------------------------------
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.46.0"
      # Documentation - Google Provider
      # https://registry.terraform.io/providers/hashicorp/aws/latest
    }

    random = {
      source  = "hashicorp/random"
      version = "3.9.0"
      # Documentation - Random Provider
      # https://registry.terraform.io/providers/hashicorp/random/latest
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.9"
      # Documentation - Local Provider
      # https://registry.terraform.io/providers/hashicorp/local/latest
    }
  }
}

provider "aws" {
  region  = "us-west-2"
  profile = "default"
}

provider "random" {
  # no config needed
}

provider "local" {
  # no config needed
}
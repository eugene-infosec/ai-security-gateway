terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2" 
}

# DYNAMODB: PK/SK Schema
resource "aws_dynamodb_table" "docs" {
  name         = "ai-gateway-docs-dev"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  # FIX: Multi-line formatting is required for HCL blocks
  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }
}
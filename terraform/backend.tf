# Remote state backend configuration
# This file configures S3 backend for Terraform state storage with DynamoDB locking

terraform {
  backend "s3" {
    # S3 bucket for state storage (must be created beforehand)
    bucket = "robco-forge-terraform-state"
    
    # State file path (overridden per environment)
    key = "terraform.tfstate"
    
    # AWS region
    region = "us-east-1"
    
    # DynamoDB table for state locking (must be created beforehand)
    dynamodb_table = "robco-forge-terraform-locks"
    
    # Enable encryption at rest
    encrypt = true
    
    # Enable versioning for state file history
    # (configured on S3 bucket, not here)
  }
  
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

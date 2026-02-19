# Staging Environment Configuration

terraform {
  backend "s3" {
    bucket         = "robco-forge-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "robco-forge-terraform-locks"
    encrypt        = true
  }
  
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.region
  
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "RobCo Forge"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  environment = "staging"
  region      = var.region
  
  common_tags = {
    Environment = local.environment
    Project     = "RobCo Forge"
    ManagedBy   = "Terraform"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"
  
  environment = local.environment
  region      = local.region
  vpc_cidr    = var.vpc_cidr
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "../../modules/eks"
  
  environment                  = local.environment
  vpc_id                       = module.networking.vpc_id
  private_subnet_ids           = module.networking.private_subnet_ids
  eks_pods_security_group_id   = module.networking.eks_pods_security_group_id
  kubernetes_version           = var.kubernetes_version
  enable_public_access         = var.eks_enable_public_access
  node_group_desired_size      = var.eks_node_group_desired_size
  node_group_min_size          = var.eks_node_group_min_size
  node_group_max_size          = var.eks_node_group_max_size
  node_instance_types          = var.eks_node_instance_types
  
  tags = local.common_tags
  
  depends_on = [module.networking]
}

# RDS Module
module "rds" {
  source = "../../modules/rds"
  
  environment                   = local.environment
  vpc_id                        = module.networking.vpc_id
  private_subnet_ids            = module.networking.private_subnet_ids
  eks_pods_security_group_id    = module.networking.eks_pods_security_group_id
  instance_class                = var.rds_instance_class
  read_replica_instance_class   = var.rds_read_replica_instance_class
  allocated_storage             = var.rds_allocated_storage
  max_allocated_storage         = var.rds_max_allocated_storage
  skip_final_snapshot           = var.rds_skip_final_snapshot
  
  tags = local.common_tags
  
  depends_on = [module.networking]
}

# WorkSpaces Module (creates Active Directory first)
module "workspaces" {
  source = "../../modules/workspaces"
  
  environment                   = local.environment
  vpc_id                        = module.networking.vpc_id
  private_subnet_ids            = module.networking.private_subnet_ids
  workspaces_security_group_id  = module.networking.workspaces_security_group_id
  directory_name                = var.directory_name
  directory_password            = var.directory_password
  directory_type                = var.directory_type
  directory_edition             = var.directory_edition
  default_ou                    = var.workspaces_default_ou
  
  tags = local.common_tags
  
  depends_on = [module.networking]
}

# FSx Module (uses Active Directory from WorkSpaces module)
module "fsx" {
  source = "../../modules/fsx"
  
  environment                    = local.environment
  vpc_id                         = module.networking.vpc_id
  private_subnet_ids             = module.networking.private_subnet_ids
  workspaces_security_group_id   = module.networking.workspaces_security_group_id
  eks_pods_security_group_id     = module.networking.eks_pods_security_group_id
  storage_capacity_gb            = var.fsx_storage_capacity_gb
  throughput_capacity_mbps       = var.fsx_throughput_capacity_mbps
  active_directory_domain_name   = module.workspaces.directory_name
  active_directory_dns_ips       = module.workspaces.directory_dns_ips
  active_directory_username      = var.active_directory_username
  active_directory_password      = var.directory_password  # Same as directory password
  active_directory_ou_dn         = var.active_directory_ou_dn
  
  tags = local.common_tags
  
  depends_on = [module.networking, module.workspaces]
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment           = local.environment
  region                = local.region
  log_retention_days    = var.log_retention_days
  alert_email_addresses = var.alert_email_addresses
  rds_instance_id       = module.rds.db_instance_id
  eks_cluster_name      = module.eks.cluster_name
  
  tags = local.common_tags
  
  depends_on = [module.rds, module.eks]
}

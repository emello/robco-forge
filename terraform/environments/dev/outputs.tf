# Outputs for development environment

# Networking outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.networking.private_subnet_ids
}

# EKS outputs
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_oidc_provider_arn" {
  description = "EKS OIDC provider ARN"
  value       = module.eks.oidc_provider_arn
}

# RDS outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_instance_endpoint
}

output "rds_read_replica_endpoint" {
  description = "RDS read replica endpoint"
  value       = module.rds.read_replica_endpoint
}

output "rds_password_secret_arn" {
  description = "RDS password secret ARN"
  value       = module.rds.db_password_secret_arn
}

# FSx outputs
output "fsx_file_system_id" {
  description = "FSx file system ID"
  value       = module.fsx.file_system_id
}

output "fsx_dns_name" {
  description = "FSx DNS name"
  value       = module.fsx.file_system_dns_name
}

output "fsx_svm_id" {
  description = "FSx SVM ID"
  value       = module.fsx.svm_id
}

# WorkSpaces outputs
output "workspaces_directory_id" {
  description = "WorkSpaces directory ID"
  value       = module.workspaces.workspaces_directory_id
}

output "workspaces_registration_code" {
  description = "WorkSpaces registration code"
  value       = module.workspaces.workspaces_registration_code
}

output "directory_dns_ips" {
  description = "Directory DNS IP addresses"
  value       = module.workspaces.directory_dns_ip_addresses
}

# Monitoring outputs
output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = module.monitoring.dashboard_name
}

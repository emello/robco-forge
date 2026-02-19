# Variables for staging environment

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.1.0.0/16"
}

# EKS variables
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "eks_enable_public_access" {
  description = "Enable public access to EKS API endpoint"
  type        = bool
  default     = false  # Private for staging
}

variable "eks_node_group_desired_size" {
  description = "Desired number of nodes in EKS node group"
  type        = number
  default     = 3
}

variable "eks_node_group_min_size" {
  description = "Minimum number of nodes in EKS node group"
  type        = number
  default     = 3
}

variable "eks_node_group_max_size" {
  description = "Maximum number of nodes in EKS node group"
  type        = number
  default     = 8
}

variable "eks_node_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["t3.large"]
}

# RDS variables
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large"
}

variable "rds_read_replica_instance_class" {
  description = "RDS read replica instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 500
}

variable "rds_skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = false  # Keep snapshots for staging
}

# FSx variables
variable "fsx_storage_capacity_gb" {
  description = "FSx storage capacity in GB"
  type        = number
  default     = 2048
}

variable "fsx_throughput_capacity_mbps" {
  description = "FSx throughput capacity in MB/s"
  type        = number
  default     = 256
}

variable "active_directory_domain_name" {
  description = "Active Directory domain name"
  type        = string
  default     = "staging.robco.local"
}

variable "active_directory_dns_ips" {
  description = "Active Directory DNS server IPs"
  type        = list(string)
  default     = []
}

variable "active_directory_username" {
  description = "Active Directory service account username"
  type        = string
  default     = "forge-service"
}

variable "active_directory_password" {
  description = "Active Directory service account password"
  type        = string
  sensitive   = true
}

variable "active_directory_ou_dn" {
  description = "Active Directory organizational unit distinguished name"
  type        = string
  default     = "OU=FSx,OU=Computers,DC=staging,DC=robco,DC=local"
}

# WorkSpaces variables
variable "directory_name" {
  description = "WorkSpaces directory name"
  type        = string
  default     = "staging.robco.local"
}

variable "directory_password" {
  description = "WorkSpaces directory admin password"
  type        = string
  sensitive   = true
}

variable "directory_type" {
  description = "Directory type (SimpleAD or MicrosoftAD)"
  type        = string
  default     = "MicrosoftAD"
}

variable "directory_edition" {
  description = "Directory edition for MicrosoftAD"
  type        = string
  default     = "Standard"
}

variable "workspaces_default_ou" {
  description = "Default OU for WorkSpaces"
  type        = string
  default     = "OU=WorkSpaces,OU=Computers,DC=staging,DC=robco,DC=local"
}

# Monitoring variables
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 90
}

variable "alert_email_addresses" {
  description = "Email addresses for alert notifications"
  type        = list(string)
  default     = []
}

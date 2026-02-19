# Variables for FSx module

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where FSx will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for FSx (requires at least 2 for Multi-AZ)"
  type        = list(string)
}

variable "workspaces_security_group_id" {
  description = "Security group ID for WorkSpaces (allowed to access FSx)"
  type        = string
}

variable "eks_pods_security_group_id" {
  description = "Security group ID for EKS pods (allowed to manage FSx)"
  type        = string
}

variable "storage_capacity_gb" {
  description = "Storage capacity in GB (minimum 1024 for Multi-AZ)"
  type        = number
  default     = 1024
}

variable "throughput_capacity_mbps" {
  description = "Throughput capacity in MB/s (128, 256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 256
}

variable "active_directory_domain_name" {
  description = "Active Directory domain name"
  type        = string
}

variable "active_directory_dns_ips" {
  description = "Active Directory DNS server IPs"
  type        = list(string)
}

variable "active_directory_username" {
  description = "Active Directory service account username"
  type        = string
}

variable "active_directory_password" {
  description = "Active Directory service account password"
  type        = string
  sensitive   = true
}

variable "active_directory_ou_dn" {
  description = "Active Directory organizational unit distinguished name"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

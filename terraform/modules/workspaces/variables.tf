# Variables for WorkSpaces module

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where WorkSpaces will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for WorkSpaces (requires at least 2)"
  type        = list(string)
}

variable "workspaces_security_group_id" {
  description = "Security group ID for WorkSpaces"
  type        = string
}

variable "directory_name" {
  description = "Directory name (e.g., robco.local)"
  type        = string
}

variable "directory_password" {
  description = "Directory admin password"
  type        = string
  sensitive   = true
}

variable "directory_type" {
  description = "Directory type (SimpleAD or MicrosoftAD)"
  type        = string
  default     = "MicrosoftAD"
  
  validation {
    condition     = contains(["SimpleAD", "MicrosoftAD"], var.directory_type)
    error_message = "Directory type must be SimpleAD or MicrosoftAD"
  }
}

variable "directory_edition" {
  description = "Directory edition for MicrosoftAD (Standard or Enterprise)"
  type        = string
  default     = "Standard"
  
  validation {
    condition     = contains(["Standard", "Enterprise"], var.directory_edition)
    error_message = "Directory edition must be Standard or Enterprise"
  }
}

variable "directory_size" {
  description = "Directory size for SimpleAD (Small or Large)"
  type        = string
  default     = "Small"
  
  validation {
    condition     = contains(["Small", "Large"], var.directory_size)
    error_message = "Directory size must be Small or Large"
  }
}

variable "default_ou" {
  description = "Default organizational unit for WorkSpaces"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

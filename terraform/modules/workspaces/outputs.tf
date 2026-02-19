# Outputs for WorkSpaces module

output "directory_id" {
  description = "Directory Service directory ID"
  value       = aws_directory_service_directory.main.id
}

output "directory_name" {
  description = "Directory name"
  value       = aws_directory_service_directory.main.name
}

output "directory_dns_ip_addresses" {
  description = "Directory DNS IP addresses"
  value       = aws_directory_service_directory.main.dns_ip_addresses
}

output "workspaces_directory_id" {
  description = "WorkSpaces directory ID"
  value       = aws_workspaces_directory.main.id
}

output "workspaces_directory_alias" {
  description = "WorkSpaces directory alias"
  value       = aws_workspaces_directory.main.alias
}

output "workspaces_registration_code" {
  description = "WorkSpaces registration code"
  value       = aws_workspaces_directory.main.registration_code
}

output "ip_group_id" {
  description = "WorkSpaces IP group ID"
  value       = aws_workspaces_ip_group.main.id
}

output "directory_password_secret_arn" {
  description = "ARN of Secrets Manager secret containing directory password"
  value       = aws_secretsmanager_secret.directory_password.arn
}

output "workspaces_role_arn" {
  description = "ARN of IAM role for WorkSpaces"
  value       = aws_iam_role.workspaces.arn
}

# Alias for FSx module compatibility
output "directory_dns_ips" {
  description = "Directory DNS IP addresses (alias for FSx module)"
  value       = aws_directory_service_directory.main.dns_ip_addresses
}

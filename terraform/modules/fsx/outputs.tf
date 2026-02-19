# Outputs for FSx module

output "file_system_id" {
  description = "FSx file system ID"
  value       = aws_fsx_ontap_file_system.main.id
}

output "file_system_dns_name" {
  description = "FSx file system DNS name"
  value       = aws_fsx_ontap_file_system.main.dns_name
}

output "file_system_endpoints" {
  description = "FSx file system endpoints"
  value       = aws_fsx_ontap_file_system.main.endpoints
}

output "svm_id" {
  description = "Storage Virtual Machine ID"
  value       = aws_fsx_ontap_storage_virtual_machine.users.id
}

output "svm_endpoints" {
  description = "Storage Virtual Machine endpoints"
  value       = aws_fsx_ontap_storage_virtual_machine.users.endpoints
}

output "users_root_volume_id" {
  description = "Users root volume ID"
  value       = aws_fsx_ontap_volume.users_root.id
}

output "users_root_volume_path" {
  description = "Users root volume junction path"
  value       = aws_fsx_ontap_volume.users_root.junction_path
}

output "admin_password_secret_arn" {
  description = "ARN of Secrets Manager secret containing FSx admin password"
  value       = aws_secretsmanager_secret.fsx_admin_password.arn
}

output "security_group_id" {
  description = "Security group ID for FSx"
  value       = aws_security_group.fsx.id
}

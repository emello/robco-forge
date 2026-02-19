# FSx Module - FSx for NetApp ONTAP for user volumes
# Requirements: 4.4, 4.5, 20.1, 20.3

# Security group for FSx
resource "aws_security_group" "fsx" {
  name        = "${var.environment}-fsx-sg"
  description = "Security group for FSx ONTAP - allows NFS/SMB from WorkSpaces and EKS"
  vpc_id      = var.vpc_id
  
  # NFS
  ingress {
    description     = "NFS from WorkSpaces"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [var.workspaces_security_group_id]
  }
  
  ingress {
    description     = "NFS from EKS pods"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [var.eks_pods_security_group_id]
  }
  
  # SMB
  ingress {
    description     = "SMB from WorkSpaces"
    from_port       = 445
    to_port         = 445
    protocol        = "tcp"
    security_groups = [var.workspaces_security_group_id]
  }
  
  # ONTAP management
  ingress {
    description     = "ONTAP management from EKS"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [var.eks_pods_security_group_id]
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-fsx-sg"
  })
}

# KMS key for FSx encryption
resource "aws_kms_key" "fsx" {
  description             = "KMS key for FSx ONTAP encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-fsx-kms-key"
  })
}

resource "aws_kms_alias" "fsx" {
  name          = "alias/${var.environment}-fsx"
  target_key_id = aws_kms_key.fsx.key_id
}

# FSx for NetApp ONTAP filesystem
resource "aws_fsx_ontap_file_system" "main" {
  storage_capacity    = var.storage_capacity_gb
  subnet_ids          = slice(var.private_subnet_ids, 0, 2)  # FSx requires exactly 2 subnets
  deployment_type     = "MULTI_AZ_1"
  throughput_capacity = var.throughput_capacity_mbps
  preferred_subnet_id = var.private_subnet_ids[0]
  
  # Encryption at rest (AES-256)
  kms_key_id = aws_kms_key.fsx.arn
  
  # Security
  security_group_ids = [aws_security_group.fsx.id]
  
  # Automated backups - daily, 30-day retention
  automatic_backup_retention_days = 30
  daily_automatic_backup_start_time = "03:00"
  weekly_maintenance_start_time     = "1:04:00"
  
  # Storage efficiency
  fsx_admin_password = random_password.fsx_admin.result
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-fsx"
  })
}

# Random password for FSx admin
resource "random_password" "fsx_admin" {
  length  = 32
  special = true
}

# Store FSx admin password in Secrets Manager
resource "aws_secretsmanager_secret" "fsx_admin_password" {
  name                    = "${var.environment}/forge/fsx/admin-password"
  description             = "Admin password for FSx ONTAP"
  recovery_window_in_days = 7
  
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "fsx_admin_password" {
  secret_id     = aws_secretsmanager_secret.fsx_admin_password.id
  secret_string = random_password.fsx_admin.result
}

# Storage Virtual Machine (SVM) for user volumes
resource "aws_fsx_ontap_storage_virtual_machine" "users" {
  file_system_id = aws_fsx_ontap_file_system.main.id
  name           = "users"
  
  # Active Directory configuration for domain-joined WorkSpaces
  active_directory_configuration {
    netbios_name = "FORGE-USERS"
    self_managed_active_directory_configuration {
      dns_ips                                = var.active_directory_dns_ips
      domain_name                            = var.active_directory_domain_name
      password                               = var.active_directory_password
      username                               = var.active_directory_username
      organizational_unit_distinguished_name = var.active_directory_ou_dn
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-users-svm"
  })
}

# Root volume for SVM with deduplication and compression
resource "aws_fsx_ontap_volume" "users_root" {
  name                       = "users_root"
  junction_path              = "/users"
  size_in_megabytes          = 1024  # 1GB root volume
  storage_efficiency_enabled = true  # Enable deduplication and compression
  storage_virtual_machine_id = aws_fsx_ontap_storage_virtual_machine.users.id
  
  # Tiering policy for cost optimization
  tiering_policy {
    name           = "AUTO"
    cooling_period = 31
  }
  
  # Root volume properties cannot be modified after creation
  lifecycle {
    ignore_changes = [junction_path, storage_efficiency_enabled, tiering_policy]
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-users-root-volume"
  })
}

# CloudWatch log group for FSx audit logs
resource "aws_cloudwatch_log_group" "fsx_audit" {
  name              = "/aws/fsx/${var.environment}-forge-fsx/audit"
  retention_in_days = 90
  
  tags = var.tags
}

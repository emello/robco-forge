# WorkSpaces Module - AWS WorkSpaces directory and configuration
# Requirements: 3.1, 3.2, 4A.1, 7.1, 7.2, 7.3, 7.4, 7.5

# AWS Directory Service - Simple AD or Microsoft AD
resource "aws_directory_service_directory" "main" {
  name     = var.directory_name
  password = var.directory_password
  type     = var.directory_type
  edition  = var.directory_type == "MicrosoftAD" ? var.directory_edition : null
  size     = var.directory_type == "SimpleAD" ? var.directory_size : null
  
  vpc_settings {
    vpc_id     = var.vpc_id
    subnet_ids = slice(var.private_subnet_ids, 0, 2)  # Requires exactly 2 subnets
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-directory"
  })
}

# Store directory password in Secrets Manager
resource "aws_secretsmanager_secret" "directory_password" {
  name                    = "${var.environment}/forge/directory/admin-password"
  description             = "Admin password for WorkSpaces directory"
  recovery_window_in_days = 7
  
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "directory_password" {
  secret_id     = aws_secretsmanager_secret.directory_password.id
  secret_string = var.directory_password
}

# Register directory with WorkSpaces
resource "aws_workspaces_directory" "main" {
  directory_id = aws_directory_service_directory.main.id
  
  # Subnet IDs for WorkSpaces (can use all private subnets)
  subnet_ids = var.private_subnet_ids
  
  # Self-service permissions (disabled for security)
  self_service_permissions {
    change_compute_type  = false
    increase_volume_size = false
    rebuild_workspace    = false
    restart_workspace    = true
    switch_running_mode  = false
  }
  
  # Workspace access properties
  workspace_access_properties {
    device_type_android    = "ALLOW"
    device_type_chromeos   = "ALLOW"
    device_type_ios        = "ALLOW"
    device_type_linux      = "ALLOW"
    device_type_osx        = "ALLOW"
    device_type_web        = "ALLOW"
    device_type_windows    = "ALLOW"
    device_type_zeroclient = "DENY"
  }
  
  # Workspace creation properties
  workspace_creation_properties {
    custom_security_group_id            = var.workspaces_security_group_id
    default_ou                          = var.default_ou
    enable_internet_access              = false  # No direct internet access
    enable_maintenance_mode             = true
    user_enabled_as_local_administrator = false  # Security: no local admin
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-workspaces-directory"
  })
}

# IP Group for access control (optional - can restrict by IP)
resource "aws_workspaces_ip_group" "main" {
  name        = "${var.environment}-forge-ip-group"
  description = "IP group for WorkSpaces access control"
  
  # Allow all IPs by default (can be restricted per requirements)
  rules {
    source      = "0.0.0.0/0"
    description = "Allow all IPs"
  }
  
  tags = var.tags
}

# Associate IP group with directory
# Note: IP group association is managed through the directory configuration
# The aws_workspaces_directory resource handles IP access control rules directly
# resource "aws_workspaces_directory_ip_group_association" "main" {
#   directory_id = aws_workspaces_directory.main.id
#   group_ids    = [aws_workspaces_ip_group.main.id]
# }

# CloudWatch log group for WorkSpaces events
resource "aws_cloudwatch_log_group" "workspaces" {
  name              = "/aws/workspaces/${var.environment}-forge"
  retention_in_days = 90
  
  tags = var.tags
}

# IAM role for WorkSpaces
resource "aws_iam_role" "workspaces" {
  name = "${var.environment}-workspaces-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "workspaces.amazonaws.com"
      }
    }]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "workspaces_default" {
  role       = aws_iam_role.workspaces.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonWorkSpacesServiceAccess"
}

resource "aws_iam_role_policy_attachment" "workspaces_self_service" {
  role       = aws_iam_role.workspaces.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonWorkSpacesSelfServiceAccess"
}

# Custom policy for WorkSpaces to access FSx
resource "aws_iam_role_policy" "workspaces_fsx_access" {
  name = "${var.environment}-workspaces-fsx-access"
  role = aws_iam_role.workspaces.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "fsx:DescribeFileSystems",
        "fsx:DescribeVolumes",
        "fsx:DescribeStorageVirtualMachines"
      ]
      Resource = "*"
    }]
  })
}

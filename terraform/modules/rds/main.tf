# RDS Module - PostgreSQL database for metadata and audit logs
# Requirements: 10.3

# DB subnet group
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-forge-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-db-subnet-group"
  })
}

# Security group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.environment}-rds-sg"
  description = "Security group for RDS PostgreSQL - allows only EKS pods"
  vpc_id      = var.vpc_id
  
  ingress {
    description     = "PostgreSQL from EKS pods"
    from_port       = 5432
    to_port         = 5432
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
    Name = "${var.environment}-rds-sg"
  })
}

# KMS key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-rds-kms-key"
  })
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.environment}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# Random password for master user
resource "random_password" "master" {
  length  = 32
  special = true
}

# Store master password in Secrets Manager
resource "aws_secretsmanager_secret" "rds_master_password" {
  name                    = "${var.environment}/forge/rds/master-password"
  description             = "Master password for RDS PostgreSQL"
  recovery_window_in_days = 7
  
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "rds_master_password" {
  secret_id     = aws_secretsmanager_secret.rds_master_password.id
  secret_string = random_password.master.result
}

# RDS PostgreSQL 15 instance with Multi-AZ
resource "aws_db_instance" "main" {
  identifier     = "${var.environment}-forge-db"
  engine         = "postgres"
  engine_version = "15.16"  # Latest available version
  instance_class = var.instance_class
  
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn
  
  db_name  = "forge"
  username = "forge_admin"
  password = random_password.master.result
  port     = 5432
  
  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  
  # Backup configuration - daily, 30-day retention
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  
  # Enable automated backups
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.environment}-forge-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  # Enable enhanced monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn
  
  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  performance_insights_retention_period = 7
  
  # Parameter group for connection pooling optimization
  parameter_group_name = aws_db_parameter_group.main.name
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-db"
  })
  
  depends_on = [aws_secretsmanager_secret_version.rds_master_password]
}

# Parameter group for PostgreSQL optimization
resource "aws_db_parameter_group" "main" {
  name   = "${var.environment}-forge-pg15"
  family = "postgres15"
  
  # Optimize for connection pooling (PgBouncer)
  parameter {
    name  = "max_connections"
    value = "200"
    apply_method = "pending-reboot"  # Static parameter requires reboot
  }
  
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4096}"
    apply_method = "pending-reboot"  # Static parameter requires reboot
  }
  
  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/2048}"
  }
  
  parameter {
    name  = "maintenance_work_mem"
    value = "2097152"  # 2GB
  }
  
  parameter {
    name  = "checkpoint_completion_target"
    value = "0.9"
  }
  
  parameter {
    name  = "wal_buffers"
    value = "16384"  # 16MB
    apply_method = "pending-reboot"  # Static parameter requires reboot
  }
  
  parameter {
    name  = "default_statistics_target"
    value = "100"
  }
  
  parameter {
    name  = "random_page_cost"
    value = "1.1"
  }
  
  parameter {
    name  = "effective_io_concurrency"
    value = "200"
  }
  
  parameter {
    name  = "work_mem"
    value = "10485"  # ~10MB
  }
  
  parameter {
    name  = "min_wal_size"
    value = "2048"  # 2GB
  }
  
  parameter {
    name  = "max_wal_size"
    value = "8192"  # 8GB
  }
  
  tags = var.tags
}

# IAM role for RDS enhanced monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.environment}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Read replica for cost queries
resource "aws_db_instance" "read_replica" {
  identifier             = "${var.environment}-forge-db-read-replica"
  replicate_source_db    = aws_db_instance.main.identifier
  instance_class         = var.read_replica_instance_class
  publicly_accessible    = false
  skip_final_snapshot    = true
  
  # Enhanced monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
  
  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-db-read-replica"
    Purpose = "cost-queries"
  })
}

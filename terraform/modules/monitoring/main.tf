# Monitoring Module - CloudWatch, Prometheus, Grafana
# Requirements: 23.1, 23.2, 23.3

# CloudWatch log groups with retention policies
resource "aws_cloudwatch_log_group" "forge_api" {
  name              = "/aws/forge/${var.environment}/api"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, {
    Name = "${var.environment}-forge-api-logs"
  })
}

resource "aws_cloudwatch_log_group" "lucy_service" {
  name              = "/aws/forge/${var.environment}/lucy"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, {
    Name = "${var.environment}-lucy-service-logs"
  })
}

resource "aws_cloudwatch_log_group" "cost_engine" {
  name              = "/aws/forge/${var.environment}/cost-engine"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, {
    Name = "${var.environment}-cost-engine-logs"
  })
}

resource "aws_cloudwatch_log_group" "provisioning_service" {
  name              = "/aws/forge/${var.environment}/provisioning"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, {
    Name = "${var.environment}-provisioning-service-logs"
  })
}

resource "aws_cloudwatch_log_group" "audit_logs" {
  name              = "/aws/forge/${var.environment}/audit"
  retention_in_days = 2557  # ~7 years for compliance (closest valid value)
  
  tags = merge(var.tags, {
    Name = "${var.environment}-audit-logs"
  })
}

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name              = "${var.environment}-forge-alerts"
  display_name      = "RobCo Forge Alerts"
  kms_master_key_id = aws_kms_key.sns.id
  
  tags = var.tags
}

# KMS key for SNS encryption
resource "aws_kms_key" "sns" {
  description             = "KMS key for SNS topic encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-sns-kms-key"
  })
}

resource "aws_kms_alias" "sns" {
  name          = "alias/${var.environment}-sns"
  target_key_id = aws_kms_key.sns.key_id
}

# SNS topic subscription for email alerts
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = length(var.alert_email_addresses)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# CloudWatch alarm - WorkSpace provisioning time > 5 minutes
resource "aws_cloudwatch_metric_alarm" "provisioning_time" {
  alarm_name          = "${var.environment}-workspace-provisioning-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ProvisioningTime"
  namespace           = "Forge/Provisioning"
  period              = 300
  statistic           = "Average"
  threshold           = 300  # 5 minutes in seconds
  alarm_description   = "WorkSpace provisioning time exceeds 5 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  tags = var.tags
}

# CloudWatch alarm - Session connection success rate < 95%
resource "aws_cloudwatch_metric_alarm" "connection_success_rate" {
  alarm_name          = "${var.environment}-session-connection-success-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConnectionSuccessRate"
  namespace           = "Forge/Sessions"
  period              = 300
  statistic           = "Average"
  threshold           = 95
  alarm_description   = "Session connection success rate below 95%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  tags = var.tags
}

# CloudWatch alarm - API error rate > 5%
resource "aws_cloudwatch_metric_alarm" "api_error_rate" {
  alarm_name          = "${var.environment}-api-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorRate"
  namespace           = "Forge/API"
  period              = 300
  statistic           = "Average"
  threshold           = 5
  alarm_description   = "API error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  tags = var.tags
}

# CloudWatch alarm - RDS CPU utilization > 80%
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.environment}-rds-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization exceeds 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }
  
  tags = var.tags
}

# CloudWatch alarm - EKS node CPU utilization > 80%
resource "aws_cloudwatch_metric_alarm" "eks_node_cpu" {
  alarm_name          = "${var.environment}-eks-node-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "node_cpu_utilization"
  namespace           = "ContainerInsights"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "EKS node CPU utilization exceeds 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ClusterName = var.eks_cluster_name
  }
  
  tags = var.tags
}

# CloudWatch dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-forge-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["Forge/Provisioning", "ProvisioningTime", { stat = "Average" }],
            [".", ".", { stat = "Maximum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "WorkSpace Provisioning Time"
          yAxis = {
            left = {
              min = 0
              max = 600
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["Forge/Sessions", "ConnectionSuccessRate"]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "Session Connection Success Rate"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["Forge/API", "RequestCount"],
            [".", "ErrorCount"]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "API Requests and Errors"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { DBInstanceIdentifier = var.rds_instance_id }],
            [".", "DatabaseConnections", { DBInstanceIdentifier = var.rds_instance_id }]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "RDS Performance"
        }
      }
    ]
  })
}

# Namespace for Prometheus (deployed via Helm in Kubernetes)
# This is a placeholder - actual Prometheus deployment happens via CDK/Helm
resource "null_resource" "prometheus_namespace" {
  provisioner "local-exec" {
    command = "echo 'Prometheus will be deployed to forge-system namespace via Helm'"
  }
}

# Namespace for Grafana (deployed via Helm in Kubernetes)
# This is a placeholder - actual Grafana deployment happens via CDK/Helm
resource "null_resource" "grafana_namespace" {
  provisioner "local-exec" {
    command = "echo 'Grafana will be deployed to forge-system namespace via Helm'"
  }
}

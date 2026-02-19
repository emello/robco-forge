# Outputs for monitoring module

output "sns_topic_arn" {
  description = "ARN of SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "cloudwatch_log_groups" {
  description = "Map of CloudWatch log group names"
  value = {
    forge_api            = aws_cloudwatch_log_group.forge_api.name
    lucy_service         = aws_cloudwatch_log_group.lucy_service.name
    cost_engine          = aws_cloudwatch_log_group.cost_engine.name
    provisioning_service = aws_cloudwatch_log_group.provisioning_service.name
    audit_logs           = aws_cloudwatch_log_group.audit_logs.name
  }
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "alarm_names" {
  description = "List of CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.provisioning_time.alarm_name,
    aws_cloudwatch_metric_alarm.connection_success_rate.alarm_name,
    aws_cloudwatch_metric_alarm.api_error_rate.alarm_name,
    aws_cloudwatch_metric_alarm.rds_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.eks_node_cpu.alarm_name
  ]
}

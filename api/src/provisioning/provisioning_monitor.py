"""Provisioning time monitoring and metrics service.

Requirements:
- 1.1: Provision WorkSpaces within 5 minutes
- 23.1: Emit provisioning time metrics
- 23.4: Alert if provisioning exceeds 5 minutes
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProvisioningStatus(Enum):
    """Provisioning status."""
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    AVAILABLE = "available"
    FAILED = "failed"


class ProvisioningMonitor:
    """Monitors WorkSpace provisioning time and emits metrics."""
    
    # SLA threshold
    PROVISIONING_SLA_SECONDS = 300  # 5 minutes
    
    def __init__(self):
        """Initialize provisioning monitor."""
        # In-memory tracking (production would use database)
        self.provisioning_requests: Dict[str, Dict[str, Any]] = {}
        
        logger.info("provisioning_monitor_initialized")
    
    def start_provisioning(
        self,
        workspace_id: str,
        user_id: str,
        blueprint_id: str,
        bundle_type: str
    ) -> Dict[str, Any]:
        """Start tracking provisioning time for a WorkSpace.
        
        Requirements:
        - Validates: Requirements 1.1 (Track provisioning time)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            blueprint_id: Blueprint identifier
            bundle_type: Bundle type
            
        Returns:
            Dictionary with tracking info
        """
        try:
            start_time = datetime.utcnow()
            
            self.provisioning_requests[workspace_id] = {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "blueprint_id": blueprint_id,
                "bundle_type": bundle_type,
                "status": ProvisioningStatus.REQUESTED.value,
                "start_time": start_time,
                "end_time": None,
                "duration_seconds": None,
                "exceeded_sla": None
            }
            
            logger.info(
                "provisioning_started",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "start_time": start_time.isoformat()
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "status": ProvisioningStatus.REQUESTED.value,
                "start_time": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "failed_to_start_provisioning_tracking",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def complete_provisioning(
        self,
        workspace_id: str,
        success: bool = True
    ) -> Dict[str, Any]:
        """Complete provisioning tracking and emit metrics.
        
        Requirements:
        - Validates: Requirements 1.1 (Provision within 5 minutes)
        - Validates: Requirements 23.1 (Emit metrics)
        - Validates: Requirements 23.4 (Alert if exceeds 5 minutes)
        
        Args:
            workspace_id: WorkSpace ID
            success: Whether provisioning succeeded
            
        Returns:
            Dictionary with provisioning results and metrics
        """
        try:
            if workspace_id not in self.provisioning_requests:
                logger.warning(
                    "provisioning_request_not_found",
                    extra={"workspace_id": workspace_id}
                )
                return {
                    "workspace_id": workspace_id,
                    "error": "provisioning_request_not_found"
                }
            
            request = self.provisioning_requests[workspace_id]
            end_time = datetime.utcnow()
            start_time = request["start_time"]
            
            duration = end_time - start_time
            duration_seconds = duration.total_seconds()
            exceeded_sla = duration_seconds > self.PROVISIONING_SLA_SECONDS
            
            # Update request
            request["end_time"] = end_time
            request["duration_seconds"] = duration_seconds
            request["exceeded_sla"] = exceeded_sla
            request["status"] = (
                ProvisioningStatus.AVAILABLE.value if success
                else ProvisioningStatus.FAILED.value
            )
            
            # Emit metrics
            self._emit_provisioning_metrics(request)
            
            # Trigger alert if SLA exceeded
            if exceeded_sla:
                self._trigger_sla_alert(request)
            
            logger.info(
                "provisioning_completed",
                extra={
                    "workspace_id": workspace_id,
                    "duration_seconds": duration_seconds,
                    "exceeded_sla": exceeded_sla,
                    "success": success
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "user_id": request["user_id"],
                "blueprint_id": request["blueprint_id"],
                "bundle_type": request["bundle_type"],
                "duration_seconds": duration_seconds,
                "exceeded_sla": exceeded_sla,
                "success": success,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "failed_to_complete_provisioning_tracking",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_provisioning_status(
        self,
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current provisioning status.
        
        Args:
            workspace_id: WorkSpace ID
            
        Returns:
            Dictionary with provisioning status or None
        """
        try:
            if workspace_id not in self.provisioning_requests:
                return None
            
            request = self.provisioning_requests[workspace_id]
            
            # Calculate current duration if still in progress
            if request["end_time"] is None:
                current_time = datetime.utcnow()
                duration = current_time - request["start_time"]
                current_duration_seconds = duration.total_seconds()
                currently_exceeding_sla = current_duration_seconds > self.PROVISIONING_SLA_SECONDS
            else:
                current_duration_seconds = request["duration_seconds"]
                currently_exceeding_sla = request["exceeded_sla"]
            
            return {
                "workspace_id": workspace_id,
                "user_id": request["user_id"],
                "blueprint_id": request["blueprint_id"],
                "bundle_type": request["bundle_type"],
                "status": request["status"],
                "start_time": request["start_time"].isoformat(),
                "current_duration_seconds": current_duration_seconds,
                "currently_exceeding_sla": currently_exceeding_sla,
                "sla_seconds": self.PROVISIONING_SLA_SECONDS
            }
            
        except Exception as e:
            logger.error(
                "failed_to_get_provisioning_status",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return None
    
    def get_provisioning_metrics(
        self,
        time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get provisioning metrics for a time period.
        
        Requirements:
        - Validates: Requirements 23.1 (Emit metrics)
        
        Args:
            time_period_hours: Time period in hours
            
        Returns:
            Dictionary with aggregated metrics
        """
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time.timestamp() - (time_period_hours * 3600)
            
            # Filter requests in time period
            recent_requests = [
                req for req in self.provisioning_requests.values()
                if req["start_time"].timestamp() >= cutoff_time
                and req["end_time"] is not None
            ]
            
            if not recent_requests:
                return {
                    "time_period_hours": time_period_hours,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "success_rate": 0.0,
                    "avg_duration_seconds": 0.0,
                    "p50_duration_seconds": 0.0,
                    "p95_duration_seconds": 0.0,
                    "p99_duration_seconds": 0.0,
                    "sla_violations": 0,
                    "sla_compliance_rate": 0.0
                }
            
            # Calculate metrics
            total_requests = len(recent_requests)
            successful_requests = sum(
                1 for req in recent_requests
                if req["status"] == ProvisioningStatus.AVAILABLE.value
            )
            failed_requests = total_requests - successful_requests
            success_rate = (successful_requests / total_requests) * 100
            
            durations = sorted([req["duration_seconds"] for req in recent_requests])
            avg_duration = sum(durations) / len(durations)
            
            # Calculate percentiles
            p50_index = int(len(durations) * 0.50)
            p95_index = int(len(durations) * 0.95)
            p99_index = int(len(durations) * 0.99)
            
            p50_duration = durations[p50_index] if p50_index < len(durations) else durations[-1]
            p95_duration = durations[p95_index] if p95_index < len(durations) else durations[-1]
            p99_duration = durations[p99_index] if p99_index < len(durations) else durations[-1]
            
            sla_violations = sum(1 for req in recent_requests if req["exceeded_sla"])
            sla_compliance_rate = ((total_requests - sla_violations) / total_requests) * 100
            
            logger.info(
                "provisioning_metrics_calculated",
                extra={
                    "time_period_hours": time_period_hours,
                    "total_requests": total_requests,
                    "success_rate": success_rate,
                    "sla_compliance_rate": sla_compliance_rate
                }
            )
            
            return {
                "time_period_hours": time_period_hours,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": success_rate,
                "avg_duration_seconds": avg_duration,
                "p50_duration_seconds": p50_duration,
                "p95_duration_seconds": p95_duration,
                "p99_duration_seconds": p99_duration,
                "sla_violations": sla_violations,
                "sla_compliance_rate": sla_compliance_rate,
                "sla_seconds": self.PROVISIONING_SLA_SECONDS
            }
            
        except Exception as e:
            logger.error(
                "failed_to_calculate_provisioning_metrics",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _emit_provisioning_metrics(
        self,
        request: Dict[str, Any]
    ) -> None:
        """Emit provisioning metrics to CloudWatch and Prometheus.
        
        Requirements:
        - Validates: Requirements 23.1 (Emit metrics)
        
        Args:
            request: Provisioning request data
        """
        try:
            # TODO: Emit to CloudWatch
            # cloudwatch.put_metric_data(
            #     Namespace='RobCoForge/Provisioning',
            #     MetricData=[{
            #         'MetricName': 'ProvisioningTime',
            #         'Value': request['duration_seconds'],
            #         'Unit': 'Seconds',
            #         'Dimensions': [
            #             {'Name': 'BundleType', 'Value': request['bundle_type']},
            #             {'Name': 'BlueprintId', 'Value': request['blueprint_id']}
            #         ]
            #     }]
            # )
            
            # TODO: Emit to Prometheus
            # provisioning_duration_seconds.labels(
            #     bundle_type=request['bundle_type'],
            #     blueprint_id=request['blueprint_id']
            # ).observe(request['duration_seconds'])
            
            logger.info(
                "provisioning_metrics_emitted",
                extra={
                    "workspace_id": request["workspace_id"],
                    "duration_seconds": request["duration_seconds"],
                    "bundle_type": request["bundle_type"],
                    "note": "Actual CloudWatch/Prometheus emission to be implemented"
                }
            )
            
        except Exception as e:
            logger.error(
                "failed_to_emit_provisioning_metrics",
                extra={
                    "workspace_id": request["workspace_id"],
                    "error": str(e)
                },
                exc_info=True
            )
    
    def _trigger_sla_alert(
        self,
        request: Dict[str, Any]
    ) -> None:
        """Trigger alert for SLA violation.
        
        Requirements:
        - Validates: Requirements 23.4 (Alert if exceeds 5 minutes)
        
        Args:
            request: Provisioning request data
        """
        try:
            # TODO: Send alert to SNS/PagerDuty/Slack
            # sns.publish(
            #     TopicArn='arn:aws:sns:region:account:robco-forge-alerts',
            #     Subject='Provisioning SLA Violation',
            #     Message=f'WorkSpace {request["workspace_id"]} exceeded 5-minute SLA'
            # )
            
            logger.warning(
                "provisioning_sla_violation_alert",
                extra={
                    "workspace_id": request["workspace_id"],
                    "user_id": request["user_id"],
                    "duration_seconds": request["duration_seconds"],
                    "sla_seconds": self.PROVISIONING_SLA_SECONDS,
                    "note": "Actual alert notification to be implemented"
                }
            )
            
        except Exception as e:
            logger.error(
                "failed_to_trigger_sla_alert",
                extra={
                    "workspace_id": request["workspace_id"],
                    "error": str(e)
                },
                exc_info=True
            )

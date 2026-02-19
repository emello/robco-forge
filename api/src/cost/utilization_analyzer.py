"""Utilization analysis service for WorkSpace optimization.

Requirements:
- 13.1: Analyze utilization over 14-day period
- 13.2: Recommend downgrade for CPU < 20% over 14 days
- 13.3: Recommend upgrade for CPU > 80% over 14 days
- 13.4: Calculate estimated cost savings/increases
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class UtilizationMetrics:
    """Container for utilization metrics."""
    
    def __init__(
        self,
        workspace_id: str,
        period_days: int,
        avg_cpu_percent: float,
        avg_memory_percent: float,
        active_hours: float,
        sample_count: int
    ):
        self.workspace_id = workspace_id
        self.period_days = period_days
        self.avg_cpu_percent = avg_cpu_percent
        self.avg_memory_percent = avg_memory_percent
        self.active_hours = active_hours
        self.sample_count = sample_count


class UtilizationAnalyzer:
    """
    Analyzes WorkSpace utilization for right-sizing recommendations.
    
    Validates:
    - Requirements 13.1: Analyze utilization over 14-day period
    - Requirements 13.2: Recommend downgrade for CPU < 20%
    - Requirements 13.3: Recommend upgrade for CPU > 80%
    - Requirements 13.4: Calculate cost savings/increases
    """
    
    # Thresholds for recommendations
    LOW_UTILIZATION_THRESHOLD = 20.0  # CPU < 20% suggests downgrade
    HIGH_UTILIZATION_THRESHOLD = 80.0  # CPU > 80% suggests upgrade
    ANALYSIS_PERIOD_DAYS = 14  # Analyze over 14 days
    
    # Bundle hierarchy for right-sizing
    BUNDLE_HIERARCHY = [
        "STANDARD",
        "PERFORMANCE",
        "POWER",
        "POWERPRO",
        "GRAPHICS_G4DN",
        "GRAPHICSPRO_G4DN"
    ]
    
    def __init__(self):
        """Initialize utilization analyzer."""
        logger.info("utilization_analyzer_initialized")
    
    def collect_metrics(
        self,
        workspace_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> UtilizationMetrics:
        """Collect CloudWatch metrics for a WorkSpace.
        
        Validates: Requirements 13.1
        
        Args:
            workspace_id: WorkSpace identifier
            start_date: Start of analysis period
            end_date: End of analysis period
            
        Returns:
            UtilizationMetrics object
            
        Note:
            In production, this would query CloudWatch for actual metrics.
            For now, returns mock data for testing.
        """
        period_days = (end_date - start_date).days
        
        # TODO: Implement actual CloudWatch metric collection
        # This is a placeholder that returns mock data
        # In production, would use boto3 to query CloudWatch:
        # - AWS/WorkSpaces CPUUtilization metric
        # - AWS/WorkSpaces MemoryUtilization metric
        # - AWS/WorkSpaces SessionLaunchTime metric
        
        logger.info(
            f"collecting_metrics workspace_id={workspace_id} "
            f"period_days={period_days}"
        )
        
        # Mock data for testing
        metrics = UtilizationMetrics(
            workspace_id=workspace_id,
            period_days=period_days,
            avg_cpu_percent=50.0,
            avg_memory_percent=60.0,
            active_hours=100.0,
            sample_count=period_days * 24  # Hourly samples
        )
        
        return metrics
    
    def analyze_workspace(
        self,
        workspace_id: str,
        current_bundle: str,
        days: int = ANALYSIS_PERIOD_DAYS
    ) -> Dict[str, Any]:
        """Analyze WorkSpace utilization over period.
        
        Validates: Requirements 13.1
        
        Args:
            workspace_id: WorkSpace identifier
            current_bundle: Current bundle type
            days: Analysis period in days (default 14)
            
        Returns:
            Dictionary with utilization analysis
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = self.collect_metrics(workspace_id, start_date, end_date)
        
        result = {
            "workspace_id": workspace_id,
            "current_bundle": current_bundle,
            "period_days": metrics.period_days,
            "avg_cpu_percent": metrics.avg_cpu_percent,
            "avg_memory_percent": metrics.avg_memory_percent,
            "active_hours": metrics.active_hours,
            "sample_count": metrics.sample_count,
            "analysis_date": datetime.now().isoformat()
        }
        
        logger.info(
            f"workspace_analyzed workspace_id={workspace_id} "
            f"avg_cpu={metrics.avg_cpu_percent:.1f}% "
            f"avg_memory={metrics.avg_memory_percent:.1f}%"
        )
        
        return result
    
    def get_recommendation(
        self,
        workspace_id: str,
        current_bundle: str,
        avg_cpu_percent: float,
        avg_memory_percent: float,
        monthly_hours: float
    ) -> Optional[Dict[str, Any]]:
        """Generate right-sizing recommendation.
        
        Validates:
        - Requirements 13.2: Downgrade for CPU < 20%
        - Requirements 13.3: Upgrade for CPU > 80%
        - Requirements 13.4: Calculate cost impact
        
        Args:
            workspace_id: WorkSpace identifier
            current_bundle: Current bundle type
            avg_cpu_percent: Average CPU utilization
            avg_memory_percent: Average memory utilization
            monthly_hours: Monthly active hours
            
        Returns:
            Recommendation dict or None if no recommendation
        """
        # Check if downgrade recommended (CPU < 20%)
        if avg_cpu_percent < self.LOW_UTILIZATION_THRESHOLD:
            target_bundle = self._get_downgrade_bundle(current_bundle)
            if target_bundle:
                return self._create_recommendation(
                    workspace_id=workspace_id,
                    current_bundle=current_bundle,
                    target_bundle=target_bundle,
                    reason="low_utilization",
                    avg_cpu_percent=avg_cpu_percent,
                    avg_memory_percent=avg_memory_percent,
                    monthly_hours=monthly_hours
                )
        
        # Check if upgrade recommended (CPU > 80%)
        elif avg_cpu_percent > self.HIGH_UTILIZATION_THRESHOLD:
            target_bundle = self._get_upgrade_bundle(current_bundle)
            if target_bundle:
                return self._create_recommendation(
                    workspace_id=workspace_id,
                    current_bundle=current_bundle,
                    target_bundle=target_bundle,
                    reason="high_utilization",
                    avg_cpu_percent=avg_cpu_percent,
                    avg_memory_percent=avg_memory_percent,
                    monthly_hours=monthly_hours
                )
        
        return None
    
    def _get_downgrade_bundle(self, current_bundle: str) -> Optional[str]:
        """Get next lower bundle in hierarchy.
        
        Args:
            current_bundle: Current bundle type
            
        Returns:
            Lower bundle type or None if already at lowest
        """
        try:
            current_index = self.BUNDLE_HIERARCHY.index(current_bundle)
            if current_index > 0:
                return self.BUNDLE_HIERARCHY[current_index - 1]
        except ValueError:
            logger.warning(f"unknown_bundle_type bundle={current_bundle}")
        
        return None
    
    def _get_upgrade_bundle(self, current_bundle: str) -> Optional[str]:
        """Get next higher bundle in hierarchy.
        
        Args:
            current_bundle: Current bundle type
            
        Returns:
            Higher bundle type or None if already at highest
        """
        try:
            current_index = self.BUNDLE_HIERARCHY.index(current_bundle)
            if current_index < len(self.BUNDLE_HIERARCHY) - 1:
                return self.BUNDLE_HIERARCHY[current_index + 1]
        except ValueError:
            logger.warning(f"unknown_bundle_type bundle={current_bundle}")
        
        return None
    
    def _create_recommendation(
        self,
        workspace_id: str,
        current_bundle: str,
        target_bundle: str,
        reason: str,
        avg_cpu_percent: float,
        avg_memory_percent: float,
        monthly_hours: float
    ) -> Dict[str, Any]:
        """Create recommendation with cost impact.
        
        Validates: Requirements 13.4
        
        Args:
            workspace_id: WorkSpace identifier
            current_bundle: Current bundle type
            target_bundle: Recommended bundle type
            reason: Reason for recommendation
            avg_cpu_percent: Average CPU utilization
            avg_memory_percent: Average memory utilization
            monthly_hours: Monthly active hours
            
        Returns:
            Recommendation dictionary
        """
        from .cost_calculator import CostCalculator
        
        calculator = CostCalculator()
        
        # Calculate cost comparison
        cost_comparison = calculator.compare_bundle_costs(
            current_bundle=current_bundle,
            target_bundle=target_bundle,
            monthly_hours=monthly_hours
        )
        
        recommendation = {
            "workspace_id": workspace_id,
            "recommendation_type": "right_sizing",
            "reason": reason,
            "current_bundle": current_bundle,
            "target_bundle": target_bundle,
            "utilization": {
                "avg_cpu_percent": avg_cpu_percent,
                "avg_memory_percent": avg_memory_percent,
                "monthly_hours": monthly_hours
            },
            "cost_impact": {
                "current_monthly_cost": cost_comparison["current_monthly_cost"],
                "target_monthly_cost": cost_comparison["target_monthly_cost"],
                "monthly_savings": cost_comparison["monthly_savings"],
                "savings_percent": cost_comparison["savings_percent"]
            },
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(
            f"recommendation_created workspace_id={workspace_id} "
            f"reason={reason} current={current_bundle} target={target_bundle} "
            f"savings=${cost_comparison['monthly_savings']:.2f}"
        )
        
        return recommendation
    
    def analyze_and_recommend(
        self,
        workspace_id: str,
        current_bundle: str,
        days: int = ANALYSIS_PERIOD_DAYS
    ) -> Dict[str, Any]:
        """Analyze utilization and generate recommendation if applicable.
        
        Combines analysis and recommendation generation.
        
        Args:
            workspace_id: WorkSpace identifier
            current_bundle: Current bundle type
            days: Analysis period in days
            
        Returns:
            Dictionary with analysis and optional recommendation
        """
        # Analyze utilization
        analysis = self.analyze_workspace(workspace_id, current_bundle, days)
        
        # Estimate monthly hours from active hours in period
        monthly_hours = (analysis["active_hours"] / analysis["period_days"]) * 30
        
        # Generate recommendation
        recommendation = self.get_recommendation(
            workspace_id=workspace_id,
            current_bundle=current_bundle,
            avg_cpu_percent=analysis["avg_cpu_percent"],
            avg_memory_percent=analysis["avg_memory_percent"],
            monthly_hours=monthly_hours
        )
        
        result = {
            "analysis": analysis,
            "recommendation": recommendation
        }
        
        return result
    
    def get_recommendations_for_workspaces(
        self,
        workspaces: List[Dict[str, Any]],
        days: int = ANALYSIS_PERIOD_DAYS
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for multiple workspaces.
        
        Args:
            workspaces: List of workspace dicts with id and bundle_type
            days: Analysis period in days
            
        Returns:
            List of recommendations (only for workspaces that need changes)
        """
        recommendations = []
        
        for workspace in workspaces:
            result = self.analyze_and_recommend(
                workspace_id=workspace["id"],
                current_bundle=workspace["bundle_type"],
                days=days
            )
            
            if result["recommendation"]:
                recommendations.append(result["recommendation"])
        
        logger.info(
            f"batch_recommendations_generated total_workspaces={len(workspaces)} "
            f"recommendations={len(recommendations)}"
        )
        
        return recommendations



class BillingModeAnalyzer:
    """
    Analyzes usage patterns to recommend optimal billing mode.
    
    Validates:
    - Requirements 15.1: Track usage hours per month
    - Requirements 15.2: Recommend monthly billing for > 80 hours/month
    - Requirements 15.3: Recommend hourly billing for < 80 hours/month
    - Requirements 15.4: Calculate cost difference between modes
    """
    
    # Threshold for billing mode recommendation
    MONTHLY_BILLING_THRESHOLD_HOURS = 80  # Hours per month
    
    # Billing mode rates (example rates)
    HOURLY_RATES = {
        "STANDARD": 0.35,
        "PERFORMANCE": 0.70,
        "POWER": 1.40,
        "POWERPRO": 2.80,
        "GRAPHICS_G4DN": 1.75,
        "GRAPHICSPRO_G4DN": 3.50,
    }
    
    MONTHLY_RATES = {
        "STANDARD": 25.00,
        "PERFORMANCE": 50.00,
        "POWER": 100.00,
        "POWERPRO": 200.00,
        "GRAPHICS_G4DN": 125.00,
        "GRAPHICSPRO_G4DN": 250.00,
    }
    
    def __init__(self):
        """Initialize billing mode analyzer."""
        logger.info("billing_mode_analyzer_initialized")
    
    def track_usage_hours(
        self,
        workspace_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Track usage hours for a workspace over period.
        
        Validates: Requirements 15.1
        
        Args:
            workspace_id: WorkSpace identifier
            start_date: Start of tracking period
            end_date: End of tracking period
            
        Returns:
            Total usage hours
            
        Note:
            In production, this would query CloudWatch for actual session hours.
            For now, returns mock data for testing.
        """
        # TODO: Implement actual CloudWatch metric collection
        # Would query AWS/WorkSpaces SessionLaunchTime and calculate active hours
        
        period_days = (end_date - start_date).days
        
        logger.info(
            f"tracking_usage_hours workspace_id={workspace_id} "
            f"period_days={period_days}"
        )
        
        # Mock data: assume 4 hours per day average
        usage_hours = period_days * 4.0
        
        return usage_hours
    
    def calculate_billing_costs(
        self,
        bundle_type: str,
        monthly_hours: float
    ) -> Dict[str, float]:
        """Calculate costs for both billing modes.
        
        Validates: Requirements 15.4
        
        Args:
            bundle_type: WorkSpace bundle type
            monthly_hours: Usage hours per month
            
        Returns:
            Dictionary with hourly_cost and monthly_cost
        """
        hourly_rate = self.HOURLY_RATES.get(bundle_type, 0.35)
        monthly_rate = self.MONTHLY_RATES.get(bundle_type, 25.00)
        
        hourly_cost = hourly_rate * monthly_hours
        monthly_cost = monthly_rate  # Fixed monthly cost
        
        return {
            "hourly_cost": hourly_cost,
            "monthly_cost": monthly_cost,
            "hourly_rate": hourly_rate,
            "monthly_rate": monthly_rate
        }
    
    def get_billing_mode_recommendation(
        self,
        workspace_id: str,
        bundle_type: str,
        monthly_hours: float,
        current_billing_mode: str = "hourly"
    ) -> Optional[Dict[str, Any]]:
        """Generate billing mode recommendation.
        
        Validates:
        - Requirements 15.2: Recommend monthly for > 80 hours/month
        - Requirements 15.3: Recommend hourly for < 80 hours/month
        - Requirements 15.4: Calculate cost difference
        
        Args:
            workspace_id: WorkSpace identifier
            bundle_type: WorkSpace bundle type
            monthly_hours: Usage hours per month
            current_billing_mode: Current billing mode (hourly or monthly)
            
        Returns:
            Recommendation dict or None if no change recommended
        """
        costs = self.calculate_billing_costs(bundle_type, monthly_hours)
        
        # Determine optimal billing mode
        if monthly_hours > self.MONTHLY_BILLING_THRESHOLD_HOURS:
            # Recommend monthly billing
            recommended_mode = "monthly"
            recommended_cost = costs["monthly_cost"]
            current_cost = costs["hourly_cost"] if current_billing_mode == "hourly" else costs["monthly_cost"]
        else:
            # Recommend hourly billing
            recommended_mode = "hourly"
            recommended_cost = costs["hourly_cost"]
            current_cost = costs["monthly_cost"] if current_billing_mode == "monthly" else costs["hourly_cost"]
        
        # Only recommend if different from current mode
        if recommended_mode == current_billing_mode:
            return None
        
        savings = current_cost - recommended_cost
        
        recommendation = {
            "workspace_id": workspace_id,
            "recommendation_type": "billing_mode",
            "current_billing_mode": current_billing_mode,
            "recommended_billing_mode": recommended_mode,
            "monthly_hours": monthly_hours,
            "bundle_type": bundle_type,
            "cost_comparison": {
                "current_cost": current_cost,
                "recommended_cost": recommended_cost,
                "monthly_savings": savings,
                "hourly_cost": costs["hourly_cost"],
                "monthly_cost": costs["monthly_cost"]
            },
            "reason": (
                f"Usage is {monthly_hours:.1f} hours/month. "
                f"{'Monthly' if recommended_mode == 'monthly' else 'Hourly'} billing "
                f"is more cost-effective."
            ),
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(
            f"billing_mode_recommendation workspace_id={workspace_id} "
            f"current={current_billing_mode} recommended={recommended_mode} "
            f"savings=${savings:.2f}"
        )
        
        return recommendation
    
    def analyze_billing_mode(
        self,
        workspace_id: str,
        bundle_type: str,
        current_billing_mode: str = "hourly",
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze usage and recommend billing mode.
        
        Args:
            workspace_id: WorkSpace identifier
            bundle_type: WorkSpace bundle type
            current_billing_mode: Current billing mode
            days: Analysis period in days
            
        Returns:
            Dictionary with analysis and recommendation
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Track usage hours
        usage_hours = self.track_usage_hours(workspace_id, start_date, end_date)
        
        # Calculate monthly hours (normalize to 30 days)
        monthly_hours = (usage_hours / days) * 30
        
        # Generate recommendation
        recommendation = self.get_billing_mode_recommendation(
            workspace_id=workspace_id,
            bundle_type=bundle_type,
            monthly_hours=monthly_hours,
            current_billing_mode=current_billing_mode
        )
        
        result = {
            "workspace_id": workspace_id,
            "bundle_type": bundle_type,
            "analysis_period_days": days,
            "total_usage_hours": usage_hours,
            "monthly_usage_hours": monthly_hours,
            "current_billing_mode": current_billing_mode,
            "recommendation": recommendation
        }
        
        return result

"""Cost calculation service for WorkSpace costs.

Requirements:
- 11.1: Real-time cost tracking
- 11.4: Track costs with 5-minute latency
- 11.5: Cost aggregation by workspace, user, team, project
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class BundleType(Enum):
    """WorkSpace bundle types with pricing."""
    STANDARD = "STANDARD"
    PERFORMANCE = "PERFORMANCE"
    POWER = "POWER"
    POWERPRO = "POWERPRO"
    GRAPHICS_G4DN = "GRAPHICS_G4DN"
    GRAPHICSPRO_G4DN = "GRAPHICSPRO_G4DN"


class CostCalculator:
    """Calculates WorkSpace costs in real-time.
    
    Requirements:
    - Validates: Requirements 11.1 (Real-time cost tracking)
    - Validates: Requirements 11.4 (5-minute latency)
    """
    
    # Hourly rates by bundle type (USD per hour)
    # Based on AWS WorkSpaces pricing as of 2024
    BUNDLE_RATES = {
        BundleType.STANDARD: 0.35,
        BundleType.PERFORMANCE: 0.70,
        BundleType.POWER: 1.40,
        BundleType.POWERPRO: 2.80,
        BundleType.GRAPHICS_G4DN: 1.75,
        BundleType.GRAPHICSPRO_G4DN: 3.50,
    }
    
    # Storage pricing (USD per GB per month)
    STORAGE_RATE_PER_GB_MONTH = 0.10
    
    # Data transfer pricing (USD per GB)
    DATA_TRANSFER_RATE_PER_GB = 0.09
    
    # Hours in a month (average)
    HOURS_PER_MONTH = 730
    
    def __init__(self):
        """Initialize cost calculator."""
        logger.info("cost_calculator_initialized")
    
    def calculate_compute_cost(
        self,
        bundle_type: str,
        running_hours: float
    ) -> float:
        """Calculate compute cost for a WorkSpace.
        
        Args:
            bundle_type: WorkSpace bundle type
            running_hours: Number of hours the WorkSpace has been running
            
        Returns:
            Compute cost in USD
            
        Raises:
            ValueError: If bundle type is invalid
        """
        try:
            bundle_enum = BundleType(bundle_type)
        except ValueError:
            logger.error(f"invalid_bundle_type bundle_type={bundle_type}")
            raise ValueError(f"Invalid bundle type: {bundle_type}")
        
        hourly_rate = self.BUNDLE_RATES[bundle_enum]
        compute_cost = hourly_rate * running_hours
        
        logger.debug(
            f"compute_cost_calculated bundle_type={bundle_type} "
            f"running_hours={running_hours} cost={compute_cost:.2f}"
        )
        
        return compute_cost
    
    def calculate_storage_cost(
        self,
        storage_gb: float,
        hours: float
    ) -> float:
        """Calculate storage cost for a WorkSpace.
        
        Args:
            storage_gb: Total storage in GB (root + user volumes)
            hours: Number of hours to calculate cost for
            
        Returns:
            Storage cost in USD
        """
        # Convert monthly rate to hourly
        hourly_storage_rate = (storage_gb * self.STORAGE_RATE_PER_GB_MONTH) / self.HOURS_PER_MONTH
        storage_cost = hourly_storage_rate * hours
        
        logger.debug(
            f"storage_cost_calculated storage_gb={storage_gb} "
            f"hours={hours} cost={storage_cost:.2f}"
        )
        
        return storage_cost
    
    def calculate_data_transfer_cost(
        self,
        data_transfer_gb: float
    ) -> float:
        """Calculate data transfer cost.
        
        Args:
            data_transfer_gb: Data transferred in GB
            
        Returns:
            Data transfer cost in USD
        """
        transfer_cost = data_transfer_gb * self.DATA_TRANSFER_RATE_PER_GB
        
        logger.debug(
            f"data_transfer_cost_calculated data_transfer_gb={data_transfer_gb} "
            f"cost={transfer_cost:.2f}"
        )
        
        return transfer_cost
    
    def calculate_workspace_cost(
        self,
        bundle_type: str,
        running_hours: float,
        storage_gb: float,
        data_transfer_gb: float = 0.0
    ) -> Dict[str, float]:
        """Calculate total cost for a WorkSpace.
        
        Requirements:
        - Validates: Requirements 11.1 (Real-time cost tracking)
        
        Args:
            bundle_type: WorkSpace bundle type
            running_hours: Number of hours the WorkSpace has been running
            storage_gb: Total storage in GB
            data_transfer_gb: Data transferred in GB
            
        Returns:
            Dictionary with cost breakdown:
            - compute_cost: Compute cost in USD
            - storage_cost: Storage cost in USD
            - data_transfer_cost: Data transfer cost in USD
            - total_cost: Total cost in USD
            
        Raises:
            ValueError: If bundle type is invalid or values are negative
        """
        if running_hours < 0:
            raise ValueError("running_hours must be non-negative")
        if storage_gb < 0:
            raise ValueError("storage_gb must be non-negative")
        if data_transfer_gb < 0:
            raise ValueError("data_transfer_gb must be non-negative")
        
        compute_cost = self.calculate_compute_cost(bundle_type, running_hours)
        storage_cost = self.calculate_storage_cost(storage_gb, running_hours)
        transfer_cost = self.calculate_data_transfer_cost(data_transfer_gb)
        
        total_cost = compute_cost + storage_cost + transfer_cost
        
        logger.info(
            f"workspace_cost_calculated bundle_type={bundle_type} "
            f"running_hours={running_hours} storage_gb={storage_gb} "
            f"data_transfer_gb={data_transfer_gb} total_cost={total_cost:.2f}"
        )
        
        return {
            "compute_cost": round(compute_cost, 2),
            "storage_cost": round(storage_cost, 2),
            "data_transfer_cost": round(transfer_cost, 2),
            "total_cost": round(total_cost, 2)
        }
    
    def estimate_monthly_cost(
        self,
        bundle_type: str,
        storage_gb: float,
        hours_per_day: float = 8.0,
        days_per_month: int = 22,
        data_transfer_gb_per_month: float = 10.0
    ) -> Dict[str, float]:
        """Estimate monthly cost for a WorkSpace.
        
        Args:
            bundle_type: WorkSpace bundle type
            storage_gb: Total storage in GB
            hours_per_day: Average hours per day
            days_per_month: Working days per month
            data_transfer_gb_per_month: Average data transfer per month
            
        Returns:
            Dictionary with monthly cost breakdown
        """
        monthly_hours = hours_per_day * days_per_month
        
        return self.calculate_workspace_cost(
            bundle_type=bundle_type,
            running_hours=monthly_hours,
            storage_gb=storage_gb,
            data_transfer_gb=data_transfer_gb_per_month
        )
    
    def estimate_daily_cost(
        self,
        bundle_type: str,
        storage_gb: float,
        operating_system: str = "LINUX",
        hours_per_day: float = 8.0,
        data_transfer_gb_per_day: float = 0.5
    ) -> float:
        """Estimate daily cost for a WorkSpace.
        
        Used for budget checking before provisioning.
        
        Args:
            bundle_type: WorkSpace bundle type
            storage_gb: Total storage in GB
            operating_system: Operating system (affects storage)
            hours_per_day: Average hours per day
            data_transfer_gb_per_day: Average data transfer per day
            
        Returns:
            Estimated daily cost in USD
        """
        cost_breakdown = self.calculate_workspace_cost(
            bundle_type=bundle_type,
            running_hours=hours_per_day,
            storage_gb=storage_gb,
            data_transfer_gb=data_transfer_gb_per_day
        )
        
        return cost_breakdown["total_cost"]
    
    def get_bundle_hourly_rate(self, bundle_type: str) -> float:
        """Get hourly rate for a bundle type.
        
        Args:
            bundle_type: WorkSpace bundle type
            
        Returns:
            Hourly rate in USD
            
        Raises:
            ValueError: If bundle type is invalid
        """
        try:
            bundle_enum = BundleType(bundle_type)
        except ValueError:
            raise ValueError(f"Invalid bundle type: {bundle_type}")
        
        return self.BUNDLE_RATES[bundle_enum]
    
    def compare_bundle_costs(
        self,
        current_bundle: str,
        target_bundle: str,
        monthly_hours: float
    ) -> Dict[str, Any]:
        """Compare costs between two bundle types.
        
        Args:
            current_bundle: Current bundle type
            target_bundle: Target bundle type
            monthly_hours: Hours per month
            
        Returns:
            Dictionary with cost comparison
        """
        current_rate = self.get_bundle_hourly_rate(current_bundle)
        target_rate = self.get_bundle_hourly_rate(target_bundle)
        
        current_cost = current_rate * monthly_hours
        target_cost = target_rate * monthly_hours
        
        savings = current_cost - target_cost
        savings_percent = (savings / current_cost * 100) if current_cost > 0 else 0
        
        return {
            "current_bundle": current_bundle,
            "target_bundle": target_bundle,
            "current_monthly_cost": round(current_cost, 2),
            "target_monthly_cost": round(target_cost, 2),
            "monthly_savings": round(savings, 2),
            "savings_percent": round(savings_percent, 1)
        }

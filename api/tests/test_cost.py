"""Unit tests for cost calculation and aggregation services."""

import pytest
from datetime import datetime, timedelta

from src.cost.cost_calculator import CostCalculator, BundleType
from src.cost.cost_aggregator import CostAggregator


class TestCostCalculator:
    """Test cost calculation service."""
    
    def test_calculate_compute_cost_standard(self):
        """Test compute cost calculation for STANDARD bundle."""
        calculator = CostCalculator()
        
        cost = calculator.calculate_compute_cost("STANDARD", 10.0)
        
        # STANDARD rate is $0.35/hour
        assert cost == 3.5
    
    def test_calculate_compute_cost_power(self):
        """Test compute cost calculation for POWER bundle."""
        calculator = CostCalculator()
        
        cost = calculator.calculate_compute_cost("POWER", 5.0)
        
        # POWER rate is $1.40/hour
        assert cost == 7.0
    
    def test_calculate_compute_cost_invalid_bundle(self):
        """Test compute cost calculation with invalid bundle type."""
        calculator = CostCalculator()
        
        with pytest.raises(ValueError, match="Invalid bundle type"):
            calculator.calculate_compute_cost("INVALID", 10.0)
    
    def test_calculate_storage_cost(self):
        """Test storage cost calculation."""
        calculator = CostCalculator()
        
        # 100 GB for 730 hours (1 month)
        cost = calculator.calculate_storage_cost(100.0, 730.0)
        
        # Storage rate is $0.10/GB/month
        # 100 GB * $0.10 = $10/month
        assert cost == 10.0
    
    def test_calculate_storage_cost_partial_month(self):
        """Test storage cost for partial month."""
        calculator = CostCalculator()
        
        # 100 GB for 365 hours (half month)
        cost = calculator.calculate_storage_cost(100.0, 365.0)
        
        # Should be half of monthly cost
        assert cost == 5.0
    
    def test_calculate_data_transfer_cost(self):
        """Test data transfer cost calculation."""
        calculator = CostCalculator()
        
        cost = calculator.calculate_data_transfer_cost(50.0)
        
        # Data transfer rate is $0.09/GB
        assert cost == 4.5
    
    def test_calculate_workspace_cost_complete(self):
        """Test complete workspace cost calculation."""
        calculator = CostCalculator()
        
        result = calculator.calculate_workspace_cost(
            bundle_type="PERFORMANCE",
            running_hours=100.0,
            storage_gb=150.0,
            data_transfer_gb=25.0
        )
        
        # PERFORMANCE rate: $0.70/hour * 100 hours = $70
        # Storage: 150 GB * $0.10/month / 730 hours * 100 hours = $2.05
        # Data transfer: 25 GB * $0.09/GB = $2.25
        # Total: $74.30
        
        assert result["compute_cost"] == 70.0
        assert result["storage_cost"] == 2.05
        assert result["data_transfer_cost"] == 2.25
        assert result["total_cost"] == 74.30
    
    def test_calculate_workspace_cost_no_data_transfer(self):
        """Test workspace cost without data transfer."""
        calculator = CostCalculator()
        
        result = calculator.calculate_workspace_cost(
            bundle_type="STANDARD",
            running_hours=50.0,
            storage_gb=80.0
        )
        
        assert result["compute_cost"] == 17.5  # $0.35 * 50
        assert result["storage_cost"] == 0.55  # 80 * 0.10 / 730 * 50
        assert result["data_transfer_cost"] == 0.0
        assert result["total_cost"] == 18.05
    
    def test_calculate_workspace_cost_negative_hours(self):
        """Test workspace cost with negative hours."""
        calculator = CostCalculator()
        
        with pytest.raises(ValueError, match="running_hours must be non-negative"):
            calculator.calculate_workspace_cost(
                bundle_type="STANDARD",
                running_hours=-10.0,
                storage_gb=100.0
            )
    
    def test_calculate_workspace_cost_negative_storage(self):
        """Test workspace cost with negative storage."""
        calculator = CostCalculator()
        
        with pytest.raises(ValueError, match="storage_gb must be non-negative"):
            calculator.calculate_workspace_cost(
                bundle_type="STANDARD",
                running_hours=10.0,
                storage_gb=-100.0
            )
    
    def test_estimate_monthly_cost_default(self):
        """Test monthly cost estimation with defaults."""
        calculator = CostCalculator()
        
        result = calculator.estimate_monthly_cost(
            bundle_type="STANDARD",
            storage_gb=100.0
        )
        
        # Default: 8 hours/day * 22 days = 176 hours
        # Compute: $0.35 * 176 = $61.60
        # Storage: 100 * $0.10 / 730 * 176 = $2.41
        # Data transfer: 10 GB * $0.09 = $0.90
        # Total: $64.91
        
        assert result["compute_cost"] == 61.60
        assert result["storage_cost"] == 2.41
        assert result["data_transfer_cost"] == 0.90
        assert result["total_cost"] == 64.91
    
    def test_estimate_monthly_cost_custom(self):
        """Test monthly cost estimation with custom values."""
        calculator = CostCalculator()
        
        result = calculator.estimate_monthly_cost(
            bundle_type="POWER",
            storage_gb=200.0,
            hours_per_day=10.0,
            days_per_month=20,
            data_transfer_gb_per_month=50.0
        )
        
        # 10 hours/day * 20 days = 200 hours
        # Compute: $1.40 * 200 = $280.00
        # Storage: 200 * $0.10 / 730 * 200 = $5.48
        # Data transfer: 50 GB * $0.09 = $4.50
        # Total: $289.98
        
        assert result["compute_cost"] == 280.00
        assert result["storage_cost"] == 5.48
        assert result["data_transfer_cost"] == 4.50
        assert result["total_cost"] == 289.98
    
    def test_get_bundle_hourly_rate(self):
        """Test getting hourly rate for bundle type."""
        calculator = CostCalculator()
        
        assert calculator.get_bundle_hourly_rate("STANDARD") == 0.35
        assert calculator.get_bundle_hourly_rate("PERFORMANCE") == 0.70
        assert calculator.get_bundle_hourly_rate("POWER") == 1.40
        assert calculator.get_bundle_hourly_rate("POWERPRO") == 2.80
        assert calculator.get_bundle_hourly_rate("GRAPHICS_G4DN") == 1.75
        assert calculator.get_bundle_hourly_rate("GRAPHICSPRO_G4DN") == 3.50
    
    def test_get_bundle_hourly_rate_invalid(self):
        """Test getting hourly rate for invalid bundle."""
        calculator = CostCalculator()
        
        with pytest.raises(ValueError, match="Invalid bundle type"):
            calculator.get_bundle_hourly_rate("INVALID")
    
    def test_compare_bundle_costs_downgrade(self):
        """Test comparing costs for downgrade."""
        calculator = CostCalculator()
        
        result = calculator.compare_bundle_costs(
            current_bundle="POWER",
            target_bundle="PERFORMANCE",
            monthly_hours=176.0
        )
        
        # POWER: $1.40 * 176 = $246.40
        # PERFORMANCE: $0.70 * 176 = $123.20
        # Savings: $123.20 (50%)
        
        assert result["current_bundle"] == "POWER"
        assert result["target_bundle"] == "PERFORMANCE"
        assert result["current_monthly_cost"] == 246.40
        assert result["target_monthly_cost"] == 123.20
        assert result["monthly_savings"] == 123.20
        assert result["savings_percent"] == 50.0
    
    def test_compare_bundle_costs_upgrade(self):
        """Test comparing costs for upgrade."""
        calculator = CostCalculator()
        
        result = calculator.compare_bundle_costs(
            current_bundle="STANDARD",
            target_bundle="POWER",
            monthly_hours=200.0
        )
        
        # STANDARD: $0.35 * 200 = $70.00
        # POWER: $1.40 * 200 = $280.00
        # Savings: -$210.00 (negative = cost increase)
        
        assert result["current_monthly_cost"] == 70.00
        assert result["target_monthly_cost"] == 280.00
        assert result["monthly_savings"] == -210.00
        assert result["savings_percent"] == -300.0


class TestCostAggregator:
    """Test cost aggregation service."""
    
    def test_aggregate_by_workspace(self):
        """Test cost aggregation by workspace."""
        aggregator = CostAggregator()
        
        workspace_ids = ["ws-1", "ws-2", "ws-3"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = aggregator.aggregate_by_workspace(workspace_ids, start_date, end_date)
        
        assert isinstance(result, dict)
        assert len(result) == 3
        assert "ws-1" in result
        assert "ws-2" in result
        assert "ws-3" in result
    
    def test_aggregate_by_user(self):
        """Test cost aggregation by user."""
        aggregator = CostAggregator()
        
        user_ids = ["user-1", "user-2"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = aggregator.aggregate_by_user(user_ids, start_date, end_date)
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "user-1" in result
        assert "user-2" in result
    
    def test_aggregate_by_team(self):
        """Test cost aggregation by team."""
        aggregator = CostAggregator()
        
        team_ids = ["team-robotics", "team-ai"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = aggregator.aggregate_by_team(team_ids, start_date, end_date)
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "team-robotics" in result
        assert "team-ai" in result
    
    def test_aggregate_by_project(self):
        """Test cost aggregation by project."""
        aggregator = CostAggregator()
        
        project_ids = ["proj-sim", "proj-ml"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = aggregator.aggregate_by_project(project_ids, start_date, end_date)
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "proj-sim" in result
        assert "proj-ml" in result
    
    def test_get_daily_costs(self):
        """Test daily cost breakdown."""
        aggregator = CostAggregator()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        result = aggregator.get_daily_costs("user-1", "user", start_date, end_date)
        
        assert isinstance(result, list)
        assert len(result) == 7  # 7 days
        assert result[0]["date"] == "2024-01-01"
        assert result[6]["date"] == "2024-01-07"
    
    def test_get_weekly_costs(self):
        """Test weekly cost breakdown."""
        aggregator = CostAggregator()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = aggregator.get_weekly_costs("team-1", "team", start_date, end_date)
        
        assert isinstance(result, list)
        assert len(result) >= 4  # At least 4 weeks in January
        assert "week_start" in result[0]
        assert "week_end" in result[0]
        assert "cost" in result[0]
    
    def test_get_monthly_costs(self):
        """Test monthly cost breakdown."""
        aggregator = CostAggregator()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 6, 30)
        
        result = aggregator.get_monthly_costs("proj-1", "project", start_date, end_date)
        
        assert isinstance(result, list)
        assert len(result) == 6  # 6 months
        assert result[0]["month"] == "2024-01"
        assert result[5]["month"] == "2024-06"
    
    def test_get_cost_breakdown(self):
        """Test detailed cost breakdown."""
        aggregator = CostAggregator()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = aggregator.get_cost_breakdown("ws-1", "workspace", start_date, end_date)
        
        assert result["entity_id"] == "ws-1"
        assert result["entity_type"] == "workspace"
        assert "compute_cost" in result
        assert "storage_cost" in result
        assert "data_transfer_cost" in result
        assert "total_cost" in result

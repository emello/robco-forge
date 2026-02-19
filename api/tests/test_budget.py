"""Unit tests for budget tracking service.

Requirements:
- 12.1: Budget configuration per team, project, and individual engineer
- 12.2: Warning at 80% threshold
- 12.3: Hard limit at 100% threshold
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.user_budget import UserBudget, BudgetScope
from src.cost.budget_tracker import BudgetTracker


# Test database setup
@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestBudgetTracker:
    """Test budget tracking service."""
    
    def test_create_budget(self, db_session):
        """Test creating a new budget."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        budget = tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        assert budget.scope == BudgetScope.USER
        assert budget.scope_id == "user-123"
        assert budget.budget_amount == 1000.0
        assert budget.current_spend == 0.0
        assert budget.warning_threshold == 0.8
        assert budget.warning_sent is False
        assert budget.hard_limit_reached is False
    
    def test_create_duplicate_budget(self, db_session):
        """Test creating duplicate budget raises error."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        with pytest.raises(ValueError, match="Budget already exists"):
            tracker.create_budget(
                scope=BudgetScope.USER,
                scope_id="user-123",
                budget_amount=2000.0,
                period_start=period_start,
                period_end=period_end
            )
    
    def test_get_budget(self, db_session):
        """Test retrieving a budget."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        created_budget = tracker.create_budget(
            scope=BudgetScope.TEAM,
            scope_id="team-robotics",
            budget_amount=5000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        retrieved_budget = tracker.get_budget(
            scope=BudgetScope.TEAM,
            scope_id="team-robotics",
            period_start=period_start,
            period_end=period_end
        )
        
        assert retrieved_budget is not None
        assert retrieved_budget.id == created_budget.id
        assert retrieved_budget.budget_amount == 5000.0
    
    def test_get_nonexistent_budget(self, db_session):
        """Test retrieving nonexistent budget returns None."""
        tracker = BudgetTracker(db_session)
        
        budget = tracker.get_budget(
            scope=BudgetScope.USER,
            scope_id="nonexistent"
        )
        
        assert budget is None
    
    def test_update_budget_spend(self, db_session):
        """Test updating budget spend."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        updated_budget = tracker.update_budget_spend(
            scope=BudgetScope.USER,
            scope_id="user-123",
            amount=250.0
        )
        
        assert updated_budget.current_spend == 250.0
        assert updated_budget.budget_utilization == 25.0
    
    def test_update_budget_spend_warning_threshold(self, db_session):
        """Test warning threshold is triggered at 80%."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        # Spend 850 (85% of budget)
        updated_budget = tracker.update_budget_spend(
            scope=BudgetScope.USER,
            scope_id="user-123",
            amount=850.0
        )
        
        assert updated_budget.current_spend == 850.0
        assert updated_budget.is_warning_threshold_reached is True
        assert updated_budget.warning_sent is True
        assert updated_budget.warning_sent_at is not None
    
    def test_update_budget_spend_hard_limit(self, db_session):
        """Test hard limit is triggered at 100%."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        # Spend 1000 (100% of budget)
        updated_budget = tracker.update_budget_spend(
            scope=BudgetScope.USER,
            scope_id="user-123",
            amount=1000.0
        )
        
        assert updated_budget.current_spend == 1000.0
        assert updated_budget.is_hard_limit_reached is True
        assert updated_budget.hard_limit_reached is True
        assert updated_budget.hard_limit_reached_at is not None
    
    def test_check_budget_allowed(self, db_session):
        """Test budget check when within limits."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        # Current spend: 0, estimated: 500
        allowed, warning, budget_info = tracker.check_budget(
            user_id="user-123",
            team_id="team-default",
            project_id=None,
            estimated_cost=500.0
        )
        
        assert allowed is True
        assert warning is None
        assert budget_info is None
    
    def test_check_budget_warning(self, db_session):
        """Test budget check with warning at 80%."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        budget = tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        # Set current spend to 700
        budget.current_spend = 700.0
        db_session.commit()
        
        # Check with estimated cost of 150 (total would be 850, 85%)
        allowed, warning, budget_info = tracker.check_budget(
            user_id="user-123",
            team_id="team-default",
            project_id=None,
            estimated_cost=150.0
        )
        
        assert allowed is True
        assert warning is not None
        assert "85.0%" in warning
        assert budget_info is None
    
    def test_check_budget_exceeded(self, db_session):
        """Test budget check when limit exceeded."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        budget = tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        # Set current spend to 950
        budget.current_spend = 950.0
        db_session.commit()
        
        # Check with estimated cost of 100 (total would be 1050, 105%)
        allowed, warning, budget_info = tracker.check_budget(
            user_id="user-123",
            team_id="team-default",
            project_id=None,
            estimated_cost=100.0
        )
        
        assert allowed is False
        assert warning is not None
        assert budget_info is not None
        assert budget_info["scope"] == "user"
        assert budget_info["current_spend"] == 950.0
        assert budget_info["estimated_cost"] == 100.0
        assert budget_info["projected_spend"] == 1050.0
    
    def test_check_budget_team_limit(self, db_session):
        """Test budget check respects team budget."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        # Create user budget with plenty of room
        tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=5000.0,
            period_start=period_start,
            period_end=period_end
        )
        
        # Create team budget that's nearly exhausted
        team_budget = tracker.create_budget(
            scope=BudgetScope.TEAM,
            scope_id="team-robotics",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        team_budget.current_spend = 980.0
        db_session.commit()
        
        # Check with estimated cost of 50 (would exceed team budget)
        allowed, warning, budget_info = tracker.check_budget(
            user_id="user-123",
            team_id="team-robotics",
            project_id=None,
            estimated_cost=50.0
        )
        
        assert allowed is False
        assert budget_info is not None
        assert budget_info["scope"] == "team"
    
    def test_get_budget_status(self, db_session):
        """Test getting budget status."""
        tracker = BudgetTracker(db_session)
        
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        budget = tracker.create_budget(
            scope=BudgetScope.USER,
            scope_id="user-123",
            budget_amount=1000.0,
            period_start=period_start,
            period_end=period_end
        )
        budget.current_spend = 750.0
        db_session.commit()
        
        status = tracker.get_budget_status(
            scope=BudgetScope.USER,
            scope_id="user-123"
        )
        
        assert status is not None
        assert status["scope"] == "USER"
        assert status["scope_id"] == "user-123"
        assert status["budget_amount"] == 1000.0
        assert status["current_spend"] == 750.0
        assert status["remaining"] == 250.0
        assert status["utilization"] == 75.0
        assert status["warning_threshold_reached"] is False
        assert status["hard_limit_reached"] is False
    
    def test_get_budget_status_nonexistent(self, db_session):
        """Test getting status for nonexistent budget."""
        tracker = BudgetTracker(db_session)
        
        status = tracker.get_budget_status(
            scope=BudgetScope.USER,
            scope_id="nonexistent"
        )
        
        assert status is None

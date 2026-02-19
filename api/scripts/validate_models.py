"""
Validation script to verify database models are correctly defined.

This script checks:
1. All models can be imported
2. All relationships are properly configured
3. All enums are defined
4. Table names and constraints are correct
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Base, WorkSpace, Blueprint, CostRecord, UserBudget, AuditLog
from src.models.workspace import ServiceType, BundleType, OperatingSystem, WorkSpaceState
from src.models.user_budget import BudgetScope
from src.models.audit_log import ActionType, ActionResult


def validate_models():
    """Validate all models are correctly defined"""
    print("Validating database models...")
    
    # Check all models are registered with Base
    tables = Base.metadata.tables
    expected_tables = {'workspaces', 'blueprints', 'cost_records', 'user_budgets', 'audit_logs'}
    actual_tables = set(tables.keys())
    
    print(f"\nExpected tables: {expected_tables}")
    print(f"Actual tables: {actual_tables}")
    
    if expected_tables == actual_tables:
        print("✓ All tables registered correctly")
    else:
        missing = expected_tables - actual_tables
        extra = actual_tables - expected_tables
        if missing:
            print(f"✗ Missing tables: {missing}")
        if extra:
            print(f"✗ Extra tables: {extra}")
        return False
    
    # Check enums
    print("\nValidating enums...")
    enums = {
        'ServiceType': ServiceType,
        'BundleType': BundleType,
        'OperatingSystem': OperatingSystem,
        'WorkSpaceState': WorkSpaceState,
        'BudgetScope': BudgetScope,
        'ActionType': ActionType,
        'ActionResult': ActionResult,
    }
    
    for name, enum_class in enums.items():
        print(f"  {name}: {[e.value for e in enum_class]}")
    print("✓ All enums defined correctly")
    
    # Check relationships
    print("\nValidating relationships...")
    
    # WorkSpace -> Blueprint
    if hasattr(WorkSpace, 'blueprint'):
        print("  ✓ WorkSpace.blueprint relationship exists")
    else:
        print("  ✗ WorkSpace.blueprint relationship missing")
        return False
    
    # WorkSpace -> CostRecord
    if hasattr(WorkSpace, 'cost_records'):
        print("  ✓ WorkSpace.cost_records relationship exists")
    else:
        print("  ✗ WorkSpace.cost_records relationship missing")
        return False
    
    # Blueprint -> WorkSpace
    if hasattr(Blueprint, 'workspaces'):
        print("  ✓ Blueprint.workspaces relationship exists")
    else:
        print("  ✗ Blueprint.workspaces relationship missing")
        return False
    
    # CostRecord -> WorkSpace
    if hasattr(CostRecord, 'workspace'):
        print("  ✓ CostRecord.workspace relationship exists")
    else:
        print("  ✗ CostRecord.workspace relationship missing")
        return False
    
    # Check indexes
    print("\nValidating indexes...")
    workspace_table = tables['workspaces']
    workspace_indexes = {idx.name for idx in workspace_table.indexes}
    print(f"  WorkSpace indexes: {workspace_indexes}")
    
    cost_table = tables['cost_records']
    cost_indexes = {idx.name for idx in cost_table.indexes}
    print(f"  CostRecord indexes: {cost_indexes}")
    
    # Check constraints
    print("\nValidating constraints...")
    blueprint_table = tables['blueprints']
    blueprint_constraints = {c.name for c in blueprint_table.constraints}
    print(f"  Blueprint constraints: {blueprint_constraints}")
    
    if 'uq_blueprint_name_version_team' in blueprint_constraints:
        print("  ✓ Blueprint unique constraint exists")
    else:
        print("  ✗ Blueprint unique constraint missing")
        return False
    
    budget_table = tables['user_budgets']
    budget_constraints = {c.name for c in budget_table.constraints}
    print(f"  UserBudget constraints: {budget_constraints}")
    
    if 'uq_budget_scope_period' in budget_constraints:
        print("  ✓ UserBudget unique constraint exists")
    else:
        print("  ✗ UserBudget unique constraint missing")
        return False
    
    print("\n✓ All validations passed!")
    return True


if __name__ == "__main__":
    success = validate_models()
    sys.exit(0 if success else 1)

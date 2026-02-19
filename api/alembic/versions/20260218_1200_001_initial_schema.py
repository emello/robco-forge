"""Initial schema with all tables, indexes, and audit log partitioning

Revision ID: 001
Revises: 
Create Date: 2026-02-18 12:00:00.000000

Requirements:
- 1.1: WorkSpace model with all fields
- 2.1: Blueprint model with version control
- 10.1, 10.2: AuditLog model with tamper-evident storage
- 10.3: Audit log partitioning by month, performance indexes
- 11.1: CostRecord model for real-time cost tracking
- 12.1: UserBudget model with threshold tracking
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE servicetype AS ENUM (
            'WORKSPACES_PERSONAL',
            'WORKSPACES_APPLICATIONS'
        )
    """)
    
    op.execute("""
        CREATE TYPE bundletype AS ENUM (
            'STANDARD',
            'PERFORMANCE',
            'POWER',
            'POWERPRO',
            'GRAPHICS_G4DN',
            'GRAPHICSPRO_G4DN'
        )
    """)
    
    op.execute("""
        CREATE TYPE operatingsystem AS ENUM (
            'WINDOWS',
            'LINUX'
        )
    """)
    
    op.execute("""
        CREATE TYPE workspacestate AS ENUM (
            'PENDING',
            'AVAILABLE',
            'STOPPED',
            'STOPPING',
            'STARTING',
            'TERMINATED'
        )
    """)
    
    op.execute("""
        CREATE TYPE budgetscope AS ENUM (
            'USER',
            'TEAM',
            'PROJECT'
        )
    """)
    
    op.execute("""
        CREATE TYPE actiontype AS ENUM (
            'WORKSPACE_PROVISION',
            'WORKSPACE_START',
            'WORKSPACE_STOP',
            'WORKSPACE_TERMINATE',
            'BLUEPRINT_CREATE',
            'BLUEPRINT_UPDATE',
            'AUTH_LOGIN',
            'AUTH_LOGOUT',
            'AUTH_FAILED',
            'LUCY_PROVISION',
            'LUCY_QUERY',
            'LUCY_ACTION',
            'BUDGET_WARNING',
            'BUDGET_LIMIT_REACHED',
            'OTHER'
        )
    """)
    
    op.execute("""
        CREATE TYPE actionresult AS ENUM (
            'SUCCESS',
            'FAILURE',
            'DENIED'
        )
    """)
    
    # Create blueprints table
    op.create_table(
        'blueprints',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bundle_id', sa.String(255), nullable=False),
        sa.Column('team_id', sa.String(255), nullable=False),
        sa.Column('configuration', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('parent_version_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('name', 'version', 'team_id', name='uq_blueprint_name_version_team')
    )
    op.create_index('ix_blueprints_team_id', 'blueprints', ['team_id'])
    
    # Create workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('service_type', sa.Enum('WORKSPACES_PERSONAL', 'WORKSPACES_APPLICATIONS', name='servicetype'), nullable=False),
        sa.Column('bundle_type', sa.Enum('STANDARD', 'PERFORMANCE', 'POWER', 'POWERPRO', 'GRAPHICS_G4DN', 'GRAPHICSPRO_G4DN', name='bundletype'), nullable=False),
        sa.Column('operating_system', sa.Enum('WINDOWS', 'LINUX', name='operatingsystem'), nullable=False),
        sa.Column('blueprint_id', sa.String(255), nullable=True),
        sa.Column('application_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('state', sa.Enum('PENDING', 'AVAILABLE', 'STOPPED', 'STOPPING', 'STARTING', 'TERMINATED', name='workspacestate'), nullable=False, server_default='PENDING'),
        sa.Column('region', sa.String(50), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('connection_url', sa.String(512), nullable=False),
        sa.Column('domain_joined', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('domain_join_status', sa.String(255), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('team_id', sa.String(255), nullable=False),
        sa.Column('cost_to_date', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('auto_stop_timeout_minutes', sa.Integer(), nullable=True),
        sa.Column('max_lifetime_days', sa.Integer(), nullable=True),
        sa.Column('last_connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('keep_alive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('stale_notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['blueprint_id'], ['blueprints.id'], ondelete='SET NULL')
    )
    op.create_index('ix_workspaces_user_id', 'workspaces', ['user_id'])
    op.create_index('ix_workspaces_team_id', 'workspaces', ['team_id'])
    
    # Create cost_records table
    op.create_table(
        'cost_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('workspace_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('team_id', sa.String(255), nullable=False),
        sa.Column('compute_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('storage_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('data_transfer_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE')
    )
    # Performance indexes for cost aggregation (Requirement 10.3)
    op.create_index('ix_cost_records_workspace_id', 'cost_records', ['workspace_id'])
    op.create_index('ix_cost_records_user_id', 'cost_records', ['user_id'])
    op.create_index('ix_cost_records_team_id', 'cost_records', ['team_id'])
    op.create_index('ix_cost_records_period_start', 'cost_records', ['period_start'])
    op.create_index('ix_cost_records_period_end', 'cost_records', ['period_end'])
    op.create_index('ix_cost_records_recorded_at', 'cost_records', ['recorded_at'])
    op.create_index('ix_cost_records_user_period', 'cost_records', ['user_id', 'period_start', 'period_end'])
    op.create_index('ix_cost_records_team_period', 'cost_records', ['team_id', 'period_start', 'period_end'])
    op.create_index('ix_cost_records_workspace_period', 'cost_records', ['workspace_id', 'period_start', 'period_end'])
    
    # Create user_budgets table
    op.create_table(
        'user_budgets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('scope', sa.Enum('USER', 'TEAM', 'PROJECT', name='budgetscope'), nullable=False),
        sa.Column('scope_id', sa.String(255), nullable=False),
        sa.Column('budget_amount', sa.Float(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_spend', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('warning_threshold', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('warning_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('warning_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hard_limit_reached', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('hard_limit_reached_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('scope', 'scope_id', 'period_start', name='uq_budget_scope_period')
    )
    op.create_index('ix_user_budgets_scope_id', 'user_budgets', ['scope_id'])
    
    # Create audit_logs table with partitioning (Requirement 10.3)
    # Note: Partitioning by month for efficient querying and archival
    op.execute("""
        CREATE TABLE audit_logs (
            id SERIAL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            user_email VARCHAR(255),
            action_type actiontype NOT NULL,
            action_description TEXT NOT NULL,
            resource_type VARCHAR(100),
            resource_id VARCHAR(255),
            result actionresult NOT NULL,
            source_ip VARCHAR(45) NOT NULL,
            user_agent TEXT,
            interface VARCHAR(50),
            context JSON NOT NULL DEFAULT '{}',
            previous_log_hash VARCHAR(64),
            log_hash VARCHAR(64) NOT NULL,
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)
    
    # Create initial partitions for current and next 12 months
    # This ensures we have partitions ready for audit log writes
    op.execute("""
        CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-02-01') TO ('2026-03-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_03 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-03-01') TO ('2026-04-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_04 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-04-01') TO ('2026-05-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_05 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_06 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_07 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_08 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-08-01') TO ('2026-09-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_09 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-09-01') TO ('2026-10-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_10 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-10-01') TO ('2026-11-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_11 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2026_12 PARTITION OF audit_logs
        FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2027_01 PARTITION OF audit_logs
        FOR VALUES FROM ('2027-01-01') TO ('2027-02-01')
    """)
    op.execute("""
        CREATE TABLE audit_logs_2027_02 PARTITION OF audit_logs
        FOR VALUES FROM ('2027-02-01') TO ('2027-03-01')
    """)
    
    # Create indexes on audit_logs (Requirement 10.3)
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action_type', 'audit_logs', ['action_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('ix_audit_logs_action_timestamp', 'audit_logs', ['action_type', 'timestamp'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('user_budgets')
    op.drop_table('cost_records')
    op.drop_table('workspaces')
    op.drop_table('blueprints')
    
    # Drop enum types
    op.execute('DROP TYPE actionresult')
    op.execute('DROP TYPE actiontype')
    op.execute('DROP TYPE budgetscope')
    op.execute('DROP TYPE workspacestate')
    op.execute('DROP TYPE operatingsystem')
    op.execute('DROP TYPE bundletype')
    op.execute('DROP TYPE servicetype')

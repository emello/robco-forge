"""
Helper script to create new audit log partitions.

This script should be run monthly (via cron or scheduled task) to create
the next month's partition before it's needed.

Requirement 10.3: Audit log partitioning by month
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from src.database import engine


def create_partition_for_month(year: int, month: int) -> None:
    """
    Create a partition for the specified year and month.
    
    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
    """
    # Calculate partition boundaries
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    partition_name = f"audit_logs_{year}_{month:02d}"
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    sql = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF audit_logs
        FOR VALUES FROM ('{start_str}') TO ('{end_str}')
    """
    
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
        print(f"Created partition: {partition_name} ({start_str} to {end_str})")


def create_next_n_months(n: int = 3) -> None:
    """
    Create partitions for the next N months.
    
    Args:
        n: Number of months ahead to create partitions for
    """
    current = datetime.now()
    
    for i in range(n):
        future = current + timedelta(days=30 * (i + 1))
        create_partition_for_month(future.year, future.month)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        n_months = int(sys.argv[1])
    else:
        n_months = 3
    
    print(f"Creating audit log partitions for next {n_months} months...")
    create_next_n_months(n_months)
    print("Done!")

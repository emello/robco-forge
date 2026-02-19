"""Pre-warmed WorkSpace pool management service.

Requirements:
- 19.1: Maintain pools of pre-provisioned WorkSpaces per blueprint
- 19.4: Replenish pool when below minimum
- 19.5: Adjust pool size based on demand patterns
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PoolWorkSpaceStatus(Enum):
    """Status of a WorkSpace in the pool."""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    PROVISIONING = "provisioning"
    FAILED = "failed"


class PoolManager:
    """Manages pre-warmed WorkSpace pools."""
    
    # Pool configuration
    DEFAULT_MIN_SIZE = 5
    DEFAULT_MAX_SIZE = 20
    
    def __init__(
        self,
        workspaces_client,
        min_pool_size: int = DEFAULT_MIN_SIZE,
        max_pool_size: int = DEFAULT_MAX_SIZE
    ):
        """Initialize pool manager.
        
        Args:
            workspaces_client: WorkSpaces API client
            min_pool_size: Minimum pool size per blueprint
            max_pool_size: Maximum pool size per blueprint
        """
        self.workspaces_client = workspaces_client
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        
        # In-memory pool state (production would use database)
        self.pools: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info(
            "pool_manager_initialized",
            extra={
                "min_pool_size": min_pool_size,
                "max_pool_size": max_pool_size
            }
        )
    
    def get_pool_key(self, blueprint_id: str, operating_system: str) -> str:
        """Generate pool key from blueprint and OS.
        
        Args:
            blueprint_id: Blueprint identifier
            operating_system: Operating system (WINDOWS or LINUX)
            
        Returns:
            Pool key string
        """
        return f"{blueprint_id}:{operating_system}"
    
    def initialize_pool(
        self,
        blueprint_id: str,
        operating_system: str,
        bundle_id: str,
        directory_id: str
    ) -> Dict[str, Any]:
        """Initialize a pre-warmed pool for a blueprint.
        
        Requirements:
        - Validates: Requirements 19.1 (Maintain pools per blueprint)
        
        Args:
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            bundle_id: WorkSpaces bundle ID
            directory_id: Active Directory ID
            
        Returns:
            Dictionary with initialization results
        """
        try:
            pool_key = self.get_pool_key(blueprint_id, operating_system)
            
            logger.info(
                "initializing_pool",
                extra={
                    "pool_key": pool_key,
                    "min_size": self.min_pool_size
                }
            )
            
            # Initialize empty pool
            self.pools[pool_key] = []
            
            # Provision initial WorkSpaces
            provisioned = self._provision_workspaces(
                pool_key=pool_key,
                blueprint_id=blueprint_id,
                operating_system=operating_system,
                bundle_id=bundle_id,
                directory_id=directory_id,
                count=self.min_pool_size
            )
            
            logger.info(
                "pool_initialized",
                extra={
                    "pool_key": pool_key,
                    "provisioned_count": len(provisioned)
                }
            )
            
            return {
                "pool_key": pool_key,
                "blueprint_id": blueprint_id,
                "operating_system": operating_system,
                "min_size": self.min_pool_size,
                "max_size": self.max_pool_size,
                "current_size": len(provisioned),
                "initialized_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "pool_initialization_failed",
                extra={
                    "blueprint_id": blueprint_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_available_workspace(
        self,
        blueprint_id: str,
        operating_system: str
    ) -> Optional[Dict[str, Any]]:
        """Get an available WorkSpace from the pool.
        
        Requirements:
        - Validates: Requirements 19.2 (Assign pre-warmed WorkSpace)
        
        Args:
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            
        Returns:
            WorkSpace info or None if pool empty
        """
        try:
            pool_key = self.get_pool_key(blueprint_id, operating_system)
            
            if pool_key not in self.pools:
                logger.warning(
                    "pool_not_found",
                    extra={"pool_key": pool_key}
                )
                return None
            
            pool = self.pools[pool_key]
            
            # Find first available WorkSpace
            for workspace in pool:
                if workspace["status"] == PoolWorkSpaceStatus.AVAILABLE.value:
                    # Mark as assigned
                    workspace["status"] = PoolWorkSpaceStatus.ASSIGNED.value
                    workspace["assigned_at"] = datetime.utcnow().isoformat()
                    
                    logger.info(
                        "workspace_assigned_from_pool",
                        extra={
                            "pool_key": pool_key,
                            "workspace_id": workspace["workspace_id"]
                        }
                    )
                    
                    return workspace
            
            logger.info(
                "no_available_workspace_in_pool",
                extra={"pool_key": pool_key}
            )
            
            return None
            
        except Exception as e:
            logger.error(
                "failed_to_get_workspace_from_pool",
                extra={
                    "blueprint_id": blueprint_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return None
    
    def replenish_pool(
        self,
        blueprint_id: str,
        operating_system: str,
        bundle_id: str,
        directory_id: str
    ) -> Dict[str, Any]:
        """Replenish pool if below minimum size.
        
        Requirements:
        - Validates: Requirements 19.4 (Replenish when below minimum)
        
        Args:
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            bundle_id: WorkSpaces bundle ID
            directory_id: Active Directory ID
            
        Returns:
            Dictionary with replenishment results
        """
        try:
            pool_key = self.get_pool_key(blueprint_id, operating_system)
            
            if pool_key not in self.pools:
                logger.warning(
                    "pool_not_found_for_replenishment",
                    extra={"pool_key": pool_key}
                )
                return {
                    "pool_key": pool_key,
                    "replenished": False,
                    "reason": "pool_not_found"
                }
            
            pool = self.pools[pool_key]
            
            # Count available WorkSpaces
            available_count = sum(
                1 for ws in pool
                if ws["status"] == PoolWorkSpaceStatus.AVAILABLE.value
            )
            
            if available_count >= self.min_pool_size:
                logger.info(
                    "pool_above_minimum",
                    extra={
                        "pool_key": pool_key,
                        "available_count": available_count,
                        "min_size": self.min_pool_size
                    }
                )
                return {
                    "pool_key": pool_key,
                    "replenished": False,
                    "reason": "above_minimum",
                    "available_count": available_count
                }
            
            # Calculate how many to provision
            needed = self.min_pool_size - available_count
            
            logger.info(
                "replenishing_pool",
                extra={
                    "pool_key": pool_key,
                    "available_count": available_count,
                    "needed": needed
                }
            )
            
            # Provision new WorkSpaces
            provisioned = self._provision_workspaces(
                pool_key=pool_key,
                blueprint_id=blueprint_id,
                operating_system=operating_system,
                bundle_id=bundle_id,
                directory_id=directory_id,
                count=needed
            )
            
            logger.info(
                "pool_replenished",
                extra={
                    "pool_key": pool_key,
                    "provisioned_count": len(provisioned)
                }
            )
            
            return {
                "pool_key": pool_key,
                "replenished": True,
                "provisioned_count": len(provisioned),
                "available_count": available_count + len(provisioned),
                "replenished_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "pool_replenishment_failed",
                extra={
                    "blueprint_id": blueprint_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_pool_status(
        self,
        blueprint_id: str,
        operating_system: str
    ) -> Dict[str, Any]:
        """Get current status of a pool.
        
        Args:
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            
        Returns:
            Dictionary with pool status
        """
        try:
            pool_key = self.get_pool_key(blueprint_id, operating_system)
            
            if pool_key not in self.pools:
                return {
                    "pool_key": pool_key,
                    "exists": False
                }
            
            pool = self.pools[pool_key]
            
            # Count by status
            status_counts = {
                "available": 0,
                "assigned": 0,
                "provisioning": 0,
                "failed": 0
            }
            
            for workspace in pool:
                status = workspace["status"]
                if status in status_counts:
                    status_counts[status] += 1
            
            return {
                "pool_key": pool_key,
                "exists": True,
                "blueprint_id": blueprint_id,
                "operating_system": operating_system,
                "min_size": self.min_pool_size,
                "max_size": self.max_pool_size,
                "total_size": len(pool),
                "status_counts": status_counts,
                "checked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "failed_to_get_pool_status",
                extra={
                    "blueprint_id": blueprint_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return {
                "pool_key": pool_key,
                "exists": False,
                "error": str(e)
            }
    
    def adjust_pool_size(
        self,
        blueprint_id: str,
        operating_system: str,
        demand_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adjust pool size based on demand patterns.
        
        Requirements:
        - Validates: Requirements 19.5 (Adjust based on demand)
        
        Args:
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            demand_pattern: Historical demand data
            
        Returns:
            Dictionary with adjustment results
        """
        try:
            pool_key = self.get_pool_key(blueprint_id, operating_system)
            
            logger.info(
                "adjusting_pool_size",
                extra={
                    "pool_key": pool_key,
                    "demand_pattern": demand_pattern
                }
            )
            
            # Simple demand-based sizing (production would use ML)
            avg_requests_per_hour = demand_pattern.get("avg_requests_per_hour", 0)
            peak_requests_per_hour = demand_pattern.get("peak_requests_per_hour", 0)
            
            # Calculate target size (peak + 20% buffer, capped at max)
            target_size = min(
                int(peak_requests_per_hour * 1.2),
                self.max_pool_size
            )
            
            # Ensure at least minimum
            target_size = max(target_size, self.min_pool_size)
            
            logger.info(
                "pool_size_adjusted",
                extra={
                    "pool_key": pool_key,
                    "target_size": target_size,
                    "avg_requests": avg_requests_per_hour,
                    "peak_requests": peak_requests_per_hour
                }
            )
            
            return {
                "pool_key": pool_key,
                "target_size": target_size,
                "avg_requests_per_hour": avg_requests_per_hour,
                "peak_requests_per_hour": peak_requests_per_hour,
                "adjusted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "pool_size_adjustment_failed",
                extra={
                    "blueprint_id": blueprint_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def _provision_workspaces(
        self,
        pool_key: str,
        blueprint_id: str,
        operating_system: str,
        bundle_id: str,
        directory_id: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Provision WorkSpaces for the pool.
        
        Args:
            pool_key: Pool identifier
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            bundle_id: WorkSpaces bundle ID
            directory_id: Active Directory ID
            count: Number of WorkSpaces to provision
            
        Returns:
            List of provisioned WorkSpace info
        """
        try:
            provisioned = []
            
            for i in range(count):
                # Generate unique username for pool WorkSpace
                username = f"pool-{blueprint_id}-{i}-{datetime.utcnow().timestamp()}"
                
                # Create WorkSpace (placeholder - actual implementation would call AWS API)
                workspace_id = f"ws-pool-{blueprint_id}-{i}"
                
                workspace_info = {
                    "workspace_id": workspace_id,
                    "blueprint_id": blueprint_id,
                    "operating_system": operating_system,
                    "bundle_id": bundle_id,
                    "directory_id": directory_id,
                    "status": PoolWorkSpaceStatus.AVAILABLE.value,
                    "created_at": datetime.utcnow().isoformat(),
                    "assigned_at": None
                }
                
                self.pools[pool_key].append(workspace_info)
                provisioned.append(workspace_info)
                
                logger.info(
                    "workspace_provisioned_for_pool",
                    extra={
                        "pool_key": pool_key,
                        "workspace_id": workspace_id
                    }
                )
            
            return provisioned
            
        except Exception as e:
            logger.error(
                "workspace_provisioning_failed",
                extra={
                    "pool_key": pool_key,
                    "count": count,
                    "error": str(e)
                },
                exc_info=True
            )
            return []

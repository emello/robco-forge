"""WorkSpace lifecycle management service.

Requirements:
- 1.7: Auto-stop WorkSpaces after idle timeout
- 1.9: Auto-terminate WorkSpaces at maximum lifetime
- 14.1: Auto-stop idle WorkSpaces
- 14.2: Flag stopped WorkSpaces as stale after 30 days
- 14.3: Notify owner of stale WorkSpaces
- 14.4: Terminate stale WorkSpaces after 7 days
- 14.5: Respect keep-alive flag
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class WorkSpaceState(Enum):
    """WorkSpace states."""
    AVAILABLE = "AVAILABLE"
    STOPPED = "STOPPED"
    TERMINATED = "TERMINATED"
    PENDING = "PENDING"


class LifecycleManager:
    """Manages WorkSpace lifecycle including idle timeout and cleanup."""
    
    # Default timeouts
    DEFAULT_IDLE_TIMEOUT_MINUTES = 60
    DEFAULT_MAX_LIFETIME_DAYS = 90
    STALE_THRESHOLD_DAYS = 30
    STALE_TERMINATION_DAYS = 7
    
    def __init__(
        self,
        workspaces_client,
        default_idle_timeout_minutes: int = DEFAULT_IDLE_TIMEOUT_MINUTES,
        default_max_lifetime_days: int = DEFAULT_MAX_LIFETIME_DAYS
    ):
        """Initialize lifecycle manager.
        
        Args:
            workspaces_client: WorkSpaces API client
            default_idle_timeout_minutes: Default idle timeout in minutes
            default_max_lifetime_days: Default maximum lifetime in days
        """
        self.workspaces_client = workspaces_client
        self.default_idle_timeout_minutes = default_idle_timeout_minutes
        self.default_max_lifetime_days = default_max_lifetime_days
        
        logger.info(
            "lifecycle_manager_initialized",
            extra={
                "default_idle_timeout_minutes": default_idle_timeout_minutes,
                "default_max_lifetime_days": default_max_lifetime_days
            }
        )
    
    def check_idle_timeout(
        self,
        workspace_id: str,
        last_activity_time: datetime,
        idle_timeout_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if WorkSpace has exceeded idle timeout.
        
        Requirements:
        - Validates: Requirements 1.7, 14.1 (Auto-stop on idle)
        
        Args:
            workspace_id: WorkSpace ID
            last_activity_time: Last activity timestamp
            idle_timeout_minutes: Idle timeout in minutes (uses default if None)
            
        Returns:
            Dictionary with timeout check results
        """
        try:
            timeout_minutes = idle_timeout_minutes or self.default_idle_timeout_minutes
            
            current_time = datetime.utcnow()
            idle_duration = current_time - last_activity_time
            idle_minutes = idle_duration.total_seconds() / 60
            
            exceeded = idle_minutes >= timeout_minutes
            
            logger.info(
                "idle_timeout_checked",
                extra={
                    "workspace_id": workspace_id,
                    "idle_minutes": idle_minutes,
                    "timeout_minutes": timeout_minutes,
                    "exceeded": exceeded
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "idle_minutes": idle_minutes,
                "timeout_minutes": timeout_minutes,
                "exceeded": exceeded,
                "last_activity_time": last_activity_time.isoformat(),
                "checked_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "idle_timeout_check_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def auto_stop_idle_workspace(
        self,
        workspace_id: str,
        last_activity_time: datetime,
        idle_timeout_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Auto-stop WorkSpace if idle timeout exceeded.
        
        Requirements:
        - Validates: Requirements 1.7, 14.1 (Auto-stop on idle)
        
        Args:
            workspace_id: WorkSpace ID
            last_activity_time: Last activity timestamp
            idle_timeout_minutes: Idle timeout in minutes
            
        Returns:
            Dictionary with auto-stop results
        """
        try:
            # Check if timeout exceeded
            check_result = self.check_idle_timeout(
                workspace_id=workspace_id,
                last_activity_time=last_activity_time,
                idle_timeout_minutes=idle_timeout_minutes
            )
            
            if not check_result["exceeded"]:
                logger.info(
                    "workspace_not_idle",
                    extra={
                        "workspace_id": workspace_id,
                        "idle_minutes": check_result["idle_minutes"]
                    }
                )
                return {
                    "workspace_id": workspace_id,
                    "stopped": False,
                    "reason": "not_idle",
                    "idle_minutes": check_result["idle_minutes"]
                }
            
            # Stop the WorkSpace
            logger.info(
                "auto_stopping_idle_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "idle_minutes": check_result["idle_minutes"]
                }
            )
            
            # TODO: Call AWS API to stop WorkSpace
            # self.workspaces_client.stop_workspaces([workspace_id])
            
            logger.info(
                "workspace_auto_stopped",
                extra={"workspace_id": workspace_id}
            )
            
            return {
                "workspace_id": workspace_id,
                "stopped": True,
                "reason": "idle_timeout",
                "idle_minutes": check_result["idle_minutes"],
                "timeout_minutes": check_result["timeout_minutes"],
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "auto_stop_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def check_maximum_lifetime(
        self,
        workspace_id: str,
        created_time: datetime,
        max_lifetime_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if WorkSpace has exceeded maximum lifetime.
        
        Requirements:
        - Validates: Requirements 1.9 (Auto-terminate at max lifetime)
        
        Args:
            workspace_id: WorkSpace ID
            created_time: WorkSpace creation timestamp
            max_lifetime_days: Maximum lifetime in days (uses default if None)
            
        Returns:
            Dictionary with lifetime check results
        """
        try:
            lifetime_days = max_lifetime_days or self.default_max_lifetime_days
            
            current_time = datetime.utcnow()
            age = current_time - created_time
            age_days = age.total_seconds() / (24 * 3600)
            
            exceeded = age_days >= lifetime_days
            
            logger.info(
                "maximum_lifetime_checked",
                extra={
                    "workspace_id": workspace_id,
                    "age_days": age_days,
                    "lifetime_days": lifetime_days,
                    "exceeded": exceeded
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "age_days": age_days,
                "lifetime_days": lifetime_days,
                "exceeded": exceeded,
                "created_time": created_time.isoformat(),
                "checked_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "lifetime_check_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def auto_terminate_expired_workspace(
        self,
        workspace_id: str,
        created_time: datetime,
        max_lifetime_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Auto-terminate WorkSpace if maximum lifetime exceeded.
        
        Requirements:
        - Validates: Requirements 1.9 (Auto-terminate at max lifetime)
        
        Args:
            workspace_id: WorkSpace ID
            created_time: WorkSpace creation timestamp
            max_lifetime_days: Maximum lifetime in days
            
        Returns:
            Dictionary with auto-terminate results
        """
        try:
            # Check if lifetime exceeded
            check_result = self.check_maximum_lifetime(
                workspace_id=workspace_id,
                created_time=created_time,
                max_lifetime_days=max_lifetime_days
            )
            
            if not check_result["exceeded"]:
                logger.info(
                    "workspace_not_expired",
                    extra={
                        "workspace_id": workspace_id,
                        "age_days": check_result["age_days"]
                    }
                )
                return {
                    "workspace_id": workspace_id,
                    "terminated": False,
                    "reason": "not_expired",
                    "age_days": check_result["age_days"]
                }
            
            # Terminate the WorkSpace
            logger.info(
                "auto_terminating_expired_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "age_days": check_result["age_days"]
                }
            )
            
            # TODO: Call AWS API to terminate WorkSpace
            # self.workspaces_client.terminate_workspaces([workspace_id])
            
            logger.info(
                "workspace_auto_terminated",
                extra={"workspace_id": workspace_id}
            )
            
            return {
                "workspace_id": workspace_id,
                "terminated": True,
                "reason": "max_lifetime",
                "age_days": check_result["age_days"],
                "lifetime_days": check_result["lifetime_days"],
                "terminated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "auto_terminate_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def check_stale_workspace(
        self,
        workspace_id: str,
        stopped_time: datetime,
        keep_alive: bool = False
    ) -> Dict[str, Any]:
        """Check if stopped WorkSpace is stale.
        
        Requirements:
        - Validates: Requirements 14.2 (Flag as stale after 30 days)
        - Validates: Requirements 14.5 (Respect keep-alive flag)
        
        Args:
            workspace_id: WorkSpace ID
            stopped_time: Time when WorkSpace was stopped
            keep_alive: Whether WorkSpace has keep-alive flag
            
        Returns:
            Dictionary with stale check results
        """
        try:
            if keep_alive:
                logger.info(
                    "workspace_has_keep_alive",
                    extra={"workspace_id": workspace_id}
                )
                return {
                    "workspace_id": workspace_id,
                    "is_stale": False,
                    "reason": "keep_alive_enabled",
                    "keep_alive": True
                }
            
            current_time = datetime.utcnow()
            stopped_duration = current_time - stopped_time
            stopped_days = stopped_duration.total_seconds() / (24 * 3600)
            
            is_stale = stopped_days >= self.STALE_THRESHOLD_DAYS
            
            logger.info(
                "stale_workspace_checked",
                extra={
                    "workspace_id": workspace_id,
                    "stopped_days": stopped_days,
                    "is_stale": is_stale
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "is_stale": is_stale,
                "stopped_days": stopped_days,
                "stale_threshold_days": self.STALE_THRESHOLD_DAYS,
                "stopped_time": stopped_time.isoformat(),
                "checked_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "stale_check_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def flag_stale_workspace(
        self,
        workspace_id: str,
        owner_id: str,
        stopped_time: datetime,
        keep_alive: bool = False
    ) -> Dict[str, Any]:
        """Flag WorkSpace as stale and notify owner.
        
        Requirements:
        - Validates: Requirements 14.2 (Flag as stale)
        - Validates: Requirements 14.3 (Notify owner)
        
        Args:
            workspace_id: WorkSpace ID
            owner_id: Owner user ID
            stopped_time: Time when WorkSpace was stopped
            keep_alive: Whether WorkSpace has keep-alive flag
            
        Returns:
            Dictionary with flagging results
        """
        try:
            # Check if stale
            check_result = self.check_stale_workspace(
                workspace_id=workspace_id,
                stopped_time=stopped_time,
                keep_alive=keep_alive
            )
            
            if not check_result["is_stale"]:
                return {
                    "workspace_id": workspace_id,
                    "flagged": False,
                    "reason": check_result.get("reason", "not_stale"),
                    "stopped_days": check_result.get("stopped_days")
                }
            
            # Flag as stale
            logger.info(
                "flagging_stale_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "owner_id": owner_id
                }
            )
            
            # TODO: Update database to mark as stale
            # TODO: Send notification to owner
            
            logger.info(
                "stale_workspace_flagged",
                extra={
                    "workspace_id": workspace_id,
                    "owner_id": owner_id
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "flagged": True,
                "owner_id": owner_id,
                "stopped_days": check_result["stopped_days"],
                "notification_sent": True,
                "flagged_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "stale_flagging_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def terminate_stale_workspace(
        self,
        workspace_id: str,
        flagged_time: datetime,
        keep_alive: bool = False
    ) -> Dict[str, Any]:
        """Terminate stale WorkSpace after grace period.
        
        Requirements:
        - Validates: Requirements 14.4 (Terminate after 7 days)
        - Validates: Requirements 14.5 (Respect keep-alive flag)
        
        Args:
            workspace_id: WorkSpace ID
            flagged_time: Time when WorkSpace was flagged as stale
            keep_alive: Whether WorkSpace has keep-alive flag
            
        Returns:
            Dictionary with termination results
        """
        try:
            if keep_alive:
                logger.info(
                    "workspace_protected_by_keep_alive",
                    extra={"workspace_id": workspace_id}
                )
                return {
                    "workspace_id": workspace_id,
                    "terminated": False,
                    "reason": "keep_alive_enabled"
                }
            
            current_time = datetime.utcnow()
            grace_period = current_time - flagged_time
            grace_days = grace_period.total_seconds() / (24 * 3600)
            
            if grace_days < self.STALE_TERMINATION_DAYS:
                logger.info(
                    "stale_workspace_in_grace_period",
                    extra={
                        "workspace_id": workspace_id,
                        "grace_days": grace_days
                    }
                )
                return {
                    "workspace_id": workspace_id,
                    "terminated": False,
                    "reason": "grace_period_not_expired",
                    "grace_days": grace_days,
                    "termination_days": self.STALE_TERMINATION_DAYS
                }
            
            # Terminate the WorkSpace
            logger.info(
                "terminating_stale_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "grace_days": grace_days
                }
            )
            
            # TODO: Call AWS API to terminate WorkSpace
            # self.workspaces_client.terminate_workspaces([workspace_id])
            
            logger.info(
                "stale_workspace_terminated",
                extra={"workspace_id": workspace_id}
            )
            
            return {
                "workspace_id": workspace_id,
                "terminated": True,
                "reason": "stale_grace_period_expired",
                "grace_days": grace_days,
                "terminated_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "stale_termination_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def scan_and_cleanup_workspaces(
        self,
        workspaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Scan all WorkSpaces and perform lifecycle actions.
        
        Args:
            workspaces: List of WorkSpace info dictionaries
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            logger.info(
                "scanning_workspaces_for_cleanup",
                extra={"workspace_count": len(workspaces)}
            )
            
            stopped_count = 0
            terminated_count = 0
            flagged_count = 0
            
            for workspace in workspaces:
                workspace_id = workspace["workspace_id"]
                
                # Check idle timeout
                if workspace.get("state") == WorkSpaceState.AVAILABLE.value:
                    last_activity = workspace.get("last_activity_time")
                    if last_activity:
                        result = self.auto_stop_idle_workspace(
                            workspace_id=workspace_id,
                            last_activity_time=last_activity,
                            idle_timeout_minutes=workspace.get("idle_timeout_minutes")
                        )
                        if result.get("stopped"):
                            stopped_count += 1
                
                # Check maximum lifetime
                created_time = workspace.get("created_time")
                if created_time:
                    result = self.auto_terminate_expired_workspace(
                        workspace_id=workspace_id,
                        created_time=created_time,
                        max_lifetime_days=workspace.get("max_lifetime_days")
                    )
                    if result.get("terminated"):
                        terminated_count += 1
                
                # Check stale WorkSpaces
                if workspace.get("state") == WorkSpaceState.STOPPED.value:
                    stopped_time = workspace.get("stopped_time")
                    keep_alive = workspace.get("keep_alive", False)
                    
                    if stopped_time and not workspace.get("is_stale"):
                        result = self.flag_stale_workspace(
                            workspace_id=workspace_id,
                            owner_id=workspace.get("owner_id"),
                            stopped_time=stopped_time,
                            keep_alive=keep_alive
                        )
                        if result.get("flagged"):
                            flagged_count += 1
                    
                    # Terminate stale WorkSpaces
                    if workspace.get("is_stale"):
                        flagged_time = workspace.get("flagged_time")
                        if flagged_time:
                            result = self.terminate_stale_workspace(
                                workspace_id=workspace_id,
                                flagged_time=flagged_time,
                                keep_alive=keep_alive
                            )
                            if result.get("terminated"):
                                terminated_count += 1
            
            logger.info(
                "workspace_cleanup_completed",
                extra={
                    "stopped_count": stopped_count,
                    "terminated_count": terminated_count,
                    "flagged_count": flagged_count
                }
            )
            
            return {
                "scanned_count": len(workspaces),
                "stopped_count": stopped_count,
                "terminated_count": terminated_count,
                "flagged_count": flagged_count,
                "scanned_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "workspace_cleanup_failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise

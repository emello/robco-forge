"""Pre-warmed WorkSpace pool assignment service.

Requirements:
- 19.2: Assign pre-warmed WorkSpace when available
- 19.3: Customize WorkSpace with user volume and config
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PoolAssignmentService:
    """Handles assignment of pre-warmed WorkSpaces to users."""
    
    def __init__(
        self,
        pool_manager,
        user_volume_service,
        secrets_service
    ):
        """Initialize pool assignment service.
        
        Args:
            pool_manager: Pool manager instance
            user_volume_service: User volume service instance
            secrets_service: Secrets service instance
        """
        self.pool_manager = pool_manager
        self.user_volume_service = user_volume_service
        self.secrets_service = secrets_service
        
        logger.info("pool_assignment_service_initialized")
    
    def assign_workspace(
        self,
        user_id: str,
        user_roles: list,
        blueprint_id: str,
        operating_system: str,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign a pre-warmed WorkSpace to a user.
        
        Requirements:
        - Validates: Requirements 19.2 (Assign pre-warmed WorkSpace)
        - Validates: Requirements 19.3 (Customize with user config)
        
        Args:
            user_id: User identifier
            user_roles: List of user roles
            blueprint_id: Blueprint identifier
            operating_system: Operating system
            team_id: Optional team identifier
            
        Returns:
            Dictionary with assignment results
        """
        try:
            logger.info(
                "assigning_workspace_from_pool",
                extra={
                    "user_id": user_id,
                    "blueprint_id": blueprint_id,
                    "operating_system": operating_system
                }
            )
            
            # Try to get WorkSpace from pool
            workspace = self.pool_manager.get_available_workspace(
                blueprint_id=blueprint_id,
                operating_system=operating_system
            )
            
            if not workspace:
                logger.info(
                    "no_workspace_available_in_pool",
                    extra={
                        "user_id": user_id,
                        "blueprint_id": blueprint_id
                    }
                )
                return {
                    "assigned": False,
                    "reason": "pool_empty",
                    "fallback_required": True
                }
            
            workspace_id = workspace["workspace_id"]
            
            # Customize WorkSpace for user
            customization_result = self._customize_workspace(
                workspace_id=workspace_id,
                user_id=user_id,
                user_roles=user_roles,
                team_id=team_id
            )
            
            if not customization_result["success"]:
                logger.error(
                    "workspace_customization_failed",
                    extra={
                        "workspace_id": workspace_id,
                        "user_id": user_id
                    }
                )
                return {
                    "assigned": False,
                    "reason": "customization_failed",
                    "workspace_id": workspace_id,
                    "error": customization_result.get("error")
                }
            
            logger.info(
                "workspace_assigned_and_customized",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id
                }
            )
            
            return {
                "assigned": True,
                "workspace_id": workspace_id,
                "blueprint_id": blueprint_id,
                "operating_system": operating_system,
                "user_id": user_id,
                "customization": customization_result
            }
            
        except Exception as e:
            logger.error(
                "workspace_assignment_failed",
                extra={
                    "user_id": user_id,
                    "blueprint_id": blueprint_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return {
                "assigned": False,
                "reason": "error",
                "error": str(e)
            }
    
    def _customize_workspace(
        self,
        workspace_id: str,
        user_id: str,
        user_roles: list,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Customize a pre-warmed WorkSpace for a specific user.
        
        Requirements:
        - Validates: Requirements 19.3 (Customize with user config)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            user_roles: List of user roles
            team_id: Optional team identifier
            
        Returns:
            Dictionary with customization results
        """
        try:
            logger.info(
                "customizing_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id
                }
            )
            
            customization_steps = []
            
            # Step 1: Attach user volume
            try:
                # Get or create user volume
                volume_id = f"fsvol-{user_id}"  # Placeholder
                
                attach_result = self.user_volume_service.attach_volume_to_workspace(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    volume_id=volume_id
                )
                
                customization_steps.append({
                    "step": "attach_user_volume",
                    "success": attach_result,
                    "volume_id": volume_id
                })
                
            except Exception as e:
                logger.error(
                    "user_volume_attachment_failed",
                    extra={
                        "workspace_id": workspace_id,
                        "error": str(e)
                    }
                )
                customization_steps.append({
                    "step": "attach_user_volume",
                    "success": False,
                    "error": str(e)
                })
            
            # Step 2: Sync dotfiles
            try:
                sync_result = self.user_volume_service.sync_dotfiles_to_workspace(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    volume_id=volume_id
                )
                
                customization_steps.append({
                    "step": "sync_dotfiles",
                    "success": sync_result.get("within_timeout", False),
                    "synced_files": sync_result.get("synced_files", [])
                })
                
            except Exception as e:
                logger.error(
                    "dotfile_sync_failed",
                    extra={
                        "workspace_id": workspace_id,
                        "error": str(e)
                    }
                )
                customization_steps.append({
                    "step": "sync_dotfiles",
                    "success": False,
                    "error": str(e)
                })
            
            # Step 3: Inject secrets
            try:
                inject_result = self.secrets_service.inject_secrets_at_launch(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    user_roles=user_roles,
                    team_id=team_id
                )
                
                customization_steps.append({
                    "step": "inject_secrets",
                    "success": True,
                    "injected_count": inject_result.get("injected_count", 0)
                })
                
            except Exception as e:
                logger.error(
                    "secret_injection_failed",
                    extra={
                        "workspace_id": workspace_id,
                        "error": str(e)
                    }
                )
                customization_steps.append({
                    "step": "inject_secrets",
                    "success": False,
                    "error": str(e)
                })
            
            # Check if all critical steps succeeded
            critical_steps = ["attach_user_volume", "inject_secrets"]
            all_critical_succeeded = all(
                step["success"]
                for step in customization_steps
                if step["step"] in critical_steps
            )
            
            logger.info(
                "workspace_customization_completed",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "success": all_critical_succeeded
                }
            )
            
            return {
                "success": all_critical_succeeded,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "steps": customization_steps
            }
            
        except Exception as e:
            logger.error(
                "workspace_customization_error",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return {
                "success": False,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "error": str(e)
            }

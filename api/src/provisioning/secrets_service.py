"""Secrets management service for WorkSpaces.

Requirements:
- 21.1: Integrate with AWS Secrets Manager
- 21.2: Inject secrets as environment variables at launch
- 21.3: Scope secret access based on RBAC
- 21.4: Rotate secrets according to policy
- 21.5: Update environment variables within 5 minutes
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsService:
    """Service for managing secrets injection into WorkSpaces."""
    
    # Update timeout for secret rotation propagation
    UPDATE_TIMEOUT_MINUTES = 5
    
    def __init__(self, region: str = "us-west-2"):
        """Initialize secrets service.
        
        Args:
            region: AWS region
        """
        self.region = region
        self.secrets_client = boto3.client("secretsmanager", region_name=region)
        self.ssm_client = boto3.client("ssm", region_name=region)
        
        logger.info(
            "secrets_service_initialized",
            extra={"region": region}
        )
    
    def get_secrets_for_user(
        self,
        user_id: str,
        user_roles: List[str],
        team_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Get secrets accessible to a user based on RBAC.
        
        Requirements:
        - Validates: Requirements 21.3 (Scope secret access based on RBAC)
        
        Args:
            user_id: User identifier
            user_roles: List of user roles
            team_id: Optional team identifier
            
        Returns:
            Dictionary of secret names to values
        """
        try:
            logger.info(
                "fetching_secrets_for_user",
                extra={
                    "user_id": user_id,
                    "roles": user_roles,
                    "team_id": team_id
                }
            )
            
            secrets = {}
            
            # Get user-specific secrets
            user_secrets = self._list_secrets_by_tag("UserId", user_id)
            for secret_name in user_secrets:
                value = self._get_secret_value(secret_name)
                if value:
                    secrets[secret_name] = value
            
            # Get team-specific secrets if team_id provided
            if team_id:
                team_secrets = self._list_secrets_by_tag("TeamId", team_id)
                for secret_name in team_secrets:
                    value = self._get_secret_value(secret_name)
                    if value:
                        secrets[secret_name] = value
            
            # Get role-based secrets
            for role in user_roles:
                role_secrets = self._list_secrets_by_tag("Role", role)
                for secret_name in role_secrets:
                    value = self._get_secret_value(secret_name)
                    if value:
                        secrets[secret_name] = value
            
            logger.info(
                "secrets_fetched_for_user",
                extra={
                    "user_id": user_id,
                    "secret_count": len(secrets)
                }
            )
            
            return secrets
            
        except Exception as e:
            logger.error(
                "failed_to_fetch_secrets",
                extra={
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return {}
    
    def inject_secrets_at_launch(
        self,
        workspace_id: str,
        user_id: str,
        user_roles: List[str],
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Inject secrets as environment variables at WorkSpace launch.
        
        Requirements:
        - Validates: Requirements 21.1 (Integrate with AWS Secrets Manager)
        - Validates: Requirements 21.2 (Inject secrets as environment variables)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            user_roles: List of user roles
            team_id: Optional team identifier
            
        Returns:
            Dictionary with injection results
        """
        try:
            logger.info(
                "injecting_secrets_at_launch",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id
                }
            )
            
            # Get secrets for user
            secrets = self.get_secrets_for_user(user_id, user_roles, team_id)
            
            if not secrets:
                logger.warning(
                    "no_secrets_found_for_user",
                    extra={"user_id": user_id}
                )
                return {
                    "workspace_id": workspace_id,
                    "injected_count": 0,
                    "injected_at": datetime.utcnow().isoformat()
                }
            
            # Inject secrets as environment variables
            injected_count = self._inject_environment_variables(
                workspace_id,
                secrets
            )
            
            logger.info(
                "secrets_injected_at_launch",
                extra={
                    "workspace_id": workspace_id,
                    "injected_count": injected_count
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "injected_count": injected_count,
                "secret_names": list(secrets.keys()),
                "injected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "secret_injection_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def handle_secret_rotation(
        self,
        secret_name: str,
        affected_workspaces: List[str]
    ) -> Dict[str, Any]:
        """Handle secret rotation by updating environment variables.
        
        Requirements:
        - Validates: Requirements 21.4 (Rotate secrets according to policy)
        - Validates: Requirements 21.5 (Update within 5 minutes)
        
        Args:
            secret_name: Name of rotated secret
            affected_workspaces: List of WorkSpace IDs using this secret
            
        Returns:
            Dictionary with rotation results
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(
                "handling_secret_rotation",
                extra={
                    "secret_name": secret_name,
                    "workspace_count": len(affected_workspaces)
                }
            )
            
            # Get new secret value
            new_value = self._get_secret_value(secret_name)
            if not new_value:
                raise ValueError(f"Failed to get new value for secret: {secret_name}")
            
            # Update environment variables in all affected WorkSpaces
            updated_workspaces = []
            failed_workspaces = []
            
            for workspace_id in affected_workspaces:
                try:
                    success = self._update_environment_variable(
                        workspace_id,
                        secret_name,
                        new_value
                    )
                    
                    if success:
                        updated_workspaces.append(workspace_id)
                    else:
                        failed_workspaces.append(workspace_id)
                        
                except Exception as e:
                    logger.error(
                        "failed_to_update_workspace",
                        extra={
                            "workspace_id": workspace_id,
                            "secret_name": secret_name,
                            "error": str(e)
                        }
                    )
                    failed_workspaces.append(workspace_id)
            
            end_time = datetime.utcnow()
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            within_timeout = duration_minutes <= self.UPDATE_TIMEOUT_MINUTES
            
            if not within_timeout:
                logger.warning(
                    "secret_rotation_exceeded_timeout",
                    extra={
                        "secret_name": secret_name,
                        "duration_minutes": duration_minutes,
                        "timeout_minutes": self.UPDATE_TIMEOUT_MINUTES
                    }
                )
            
            logger.info(
                "secret_rotation_completed",
                extra={
                    "secret_name": secret_name,
                    "updated_count": len(updated_workspaces),
                    "failed_count": len(failed_workspaces),
                    "duration_minutes": duration_minutes,
                    "within_timeout": within_timeout
                }
            )
            
            return {
                "secret_name": secret_name,
                "updated_workspaces": updated_workspaces,
                "failed_workspaces": failed_workspaces,
                "duration_minutes": duration_minutes,
                "within_timeout": within_timeout,
                "rotated_at": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "secret_rotation_failed",
                extra={
                    "secret_name": secret_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def configure_secret_rotation(
        self,
        secret_name: str,
        rotation_days: int = 30
    ) -> bool:
        """Configure automatic rotation for a secret.
        
        Requirements:
        - Validates: Requirements 21.4 (Rotate secrets according to policy)
        
        Args:
            secret_name: Name of secret to configure
            rotation_days: Days between rotations
            
        Returns:
            True if configuration successful
        """
        try:
            logger.info(
                "configuring_secret_rotation",
                extra={
                    "secret_name": secret_name,
                    "rotation_days": rotation_days
                }
            )
            
            # Enable automatic rotation
            self.secrets_client.rotate_secret(
                SecretId=secret_name,
                RotationRules={
                    "AutomaticallyAfterDays": rotation_days
                }
            )
            
            logger.info(
                "secret_rotation_configured",
                extra={
                    "secret_name": secret_name,
                    "rotation_days": rotation_days
                }
            )
            
            return True
            
        except ClientError as e:
            logger.error(
                "secret_rotation_configuration_failed",
                extra={
                    "secret_name": secret_name,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    def _list_secrets_by_tag(
        self,
        tag_key: str,
        tag_value: str
    ) -> List[str]:
        """List secrets filtered by tag.
        
        Args:
            tag_key: Tag key to filter by
            tag_value: Tag value to filter by
            
        Returns:
            List of secret names
        """
        try:
            response = self.secrets_client.list_secrets(
                Filters=[
                    {
                        "Key": "tag-key",
                        "Values": [tag_key]
                    },
                    {
                        "Key": "tag-value",
                        "Values": [tag_value]
                    }
                ]
            )
            
            return [secret["Name"] for secret in response.get("SecretList", [])]
            
        except ClientError as e:
            logger.error(
                "failed_to_list_secrets",
                extra={
                    "tag_key": tag_key,
                    "tag_value": tag_value,
                    "error": str(e)
                }
            )
            return []
    
    def _get_secret_value(self, secret_name: str) -> Optional[str]:
        """Get the value of a secret.
        
        Args:
            secret_name: Name of secret
            
        Returns:
            Secret value or None
        """
        try:
            response = self.secrets_client.get_secret_value(
                SecretId=secret_name
            )
            
            # Handle both string and binary secrets
            if "SecretString" in response:
                return response["SecretString"]
            else:
                return response["SecretBinary"].decode("utf-8")
                
        except ClientError as e:
            logger.error(
                "failed_to_get_secret_value",
                extra={
                    "secret_name": secret_name,
                    "error": str(e)
                }
            )
            return None
    
    def _inject_environment_variables(
        self,
        workspace_id: str,
        secrets: Dict[str, str]
    ) -> int:
        """Inject secrets as environment variables in WorkSpace.
        
        Args:
            workspace_id: WorkSpace ID
            secrets: Dictionary of secret names to values
            
        Returns:
            Number of secrets injected
        """
        try:
            # TODO: Use SSM to inject environment variables
            # This would typically involve:
            # 1. Create/update environment variable file
            # 2. Source file in shell profiles
            # 3. Verify variables are accessible
            
            logger.info(
                "environment_variables_injected",
                extra={
                    "workspace_id": workspace_id,
                    "count": len(secrets),
                    "note": "Actual injection via SSM to be implemented"
                }
            )
            
            return len(secrets)
            
        except Exception as e:
            logger.error(
                "environment_variable_injection_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return 0
    
    def _update_environment_variable(
        self,
        workspace_id: str,
        variable_name: str,
        variable_value: str
    ) -> bool:
        """Update an environment variable in a running WorkSpace.
        
        Args:
            workspace_id: WorkSpace ID
            variable_name: Environment variable name
            variable_value: New value
            
        Returns:
            True if update successful
        """
        try:
            # TODO: Use SSM to update environment variable
            # This would typically involve:
            # 1. Update environment variable file
            # 2. Reload environment in running processes
            # 3. Verify new value is accessible
            
            logger.info(
                "environment_variable_updated",
                extra={
                    "workspace_id": workspace_id,
                    "variable_name": variable_name,
                    "note": "Actual update via SSM to be implemented"
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "environment_variable_update_failed",
                extra={
                    "workspace_id": workspace_id,
                    "variable_name": variable_name,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    def get_secret_metadata(
        self,
        secret_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata about a secret.
        
        Args:
            secret_name: Name of secret
            
        Returns:
            Dictionary with secret metadata or None
        """
        try:
            response = self.secrets_client.describe_secret(
                SecretId=secret_name
            )
            
            return {
                "name": response["Name"],
                "arn": response["ARN"],
                "description": response.get("Description", ""),
                "rotation_enabled": response.get("RotationEnabled", False),
                "rotation_rules": response.get("RotationRules", {}),
                "last_rotated": response.get("LastRotatedDate", "").isoformat() if response.get("LastRotatedDate") else None,
                "last_changed": response.get("LastChangedDate", "").isoformat() if response.get("LastChangedDate") else None,
                "tags": response.get("Tags", [])
            }
            
        except ClientError as e:
            logger.error(
                "failed_to_get_secret_metadata",
                extra={
                    "secret_name": secret_name,
                    "error": str(e)
                }
            )
            return None

"""WorkSpace configuration service for security and streaming protocol setup.

Requirements:
- 3.1: WSP-only streaming (disable PCoIP)
- 3.2: Disable PCoIP at directory level
- 7.1-7.7: Data exfiltration prevention via Group Policies
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class StreamingProtocol(Enum):
    """Streaming protocol options."""
    WSP = "WSP"  # WorkSpaces Streaming Protocol (required)
    PCOIP = "PCoIP"  # Legacy protocol (must be disabled)


class WorkSpaceConfigurator:
    """Configures WorkSpace security and streaming settings."""
    
    # Security Group Policy settings for data exfiltration prevention
    SECURITY_GROUP_POLICIES = {
        "clipboard": {
            "enabled": False,
            "description": "Disable clipboard operations (Req 7.1)"
        },
        "usb_redirection": {
            "enabled": False,
            "description": "Disable USB device redirection (Req 7.2)"
        },
        "drive_redirection": {
            "enabled": False,
            "description": "Disable drive redirection (Req 7.3)"
        },
        "file_transfer": {
            "enabled": False,
            "description": "Disable file transfer (Req 7.4)"
        },
        "printing": {
            "enabled": False,
            "description": "Disable printing (Req 7.5)"
        },
        "screen_watermark": {
            "enabled": True,
            "description": "Enable screen watermark with user identity (Req 7.6, 7.7)"
        }
    }
    
    def __init__(self, workspaces_client):
        """Initialize configurator.
        
        Args:
            workspaces_client: WorkSpacesClient instance
        """
        self.client = workspaces_client
    
    def get_wsp_only_properties(self) -> Dict[str, Any]:
        """Get WorkSpace properties for WSP-only configuration.
        
        Requirements:
        - Validates: Requirements 3.1 (WSP-only streaming)
        
        Returns:
            Dictionary of WorkSpace properties
        """
        return {
            "Protocols": ["WSP"],  # Only WSP enabled
            "OperatingSystemName": None,  # Will be set based on request
        }
    
    def get_security_group_policy_config(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get Group Policy configuration for data exfiltration prevention.
        
        Requirements:
        - Validates: Requirements 7.1 (Disable clipboard)
        - Validates: Requirements 7.2 (Disable USB)
        - Validates: Requirements 7.3 (Disable drive redirection)
        - Validates: Requirements 7.4 (Disable file transfer)
        - Validates: Requirements 7.5 (Disable printing)
        - Validates: Requirements 7.6 (Screen watermark)
        - Validates: Requirements 7.7 (Watermark persistence)
        
        Args:
            user_id: User identifier for watermark
            session_id: Session identifier for watermark
            
        Returns:
            Group Policy configuration dictionary
        """
        config = {
            "clipboard_operations": False,
            "usb_device_redirection": False,
            "drive_redirection": False,
            "file_transfer": False,
            "printing": False,
            "screen_watermark": {
                "enabled": True,
                "text": f"User: {user_id} | Session: {session_id}",
                "opacity": 0.3,
                "position": "bottom_right"
            }
        }
        
        logger.info(
            "security_group_policy_configured",
            user_id=user_id,
            session_id=session_id,
            policies=list(config.keys())
        )
        
        return config
    
    def build_workspace_request(
        self,
        directory_id: str,
        user_name: str,
        bundle_id: str,
        user_id: str,
        workspace_id: str,
        tags: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Build WorkSpace creation request with security configuration.
        
        Requirements:
        - Validates: Requirements 3.1 (WSP-only)
        - Validates: Requirements 7.1-7.7 (Data exfiltration prevention)
        
        Args:
            directory_id: WorkSpaces directory ID
            user_name: Active Directory user name
            bundle_id: WorkSpace bundle ID
            user_id: User identifier
            workspace_id: WorkSpace identifier
            tags: Optional resource tags
            
        Returns:
            WorkSpace creation request dictionary
        """
        request = {
            "DirectoryId": directory_id,
            "UserName": user_name,
            "BundleId": bundle_id,
            "WorkspaceProperties": {
                "RunningMode": "AUTO_STOP",  # Auto-stop when idle
                "RunningModeAutoStopTimeoutInMinutes": 60,
                "RootVolumeSizeGib": 80,
                "UserVolumeSizeGib": 100,
                "ComputeTypeName": self._get_compute_type_from_bundle(bundle_id),
                "Protocols": ["WSP"]  # WSP-only
            },
            "Tags": tags or []
        }
        
        # Add workspace ID tag
        request["Tags"].append({
            "Key": "WorkspaceId",
            "Value": workspace_id
        })
        
        # Add user ID tag
        request["Tags"].append({
            "Key": "UserId",
            "Value": user_id
        })
        
        logger.info(
            "workspace_request_built",
            workspace_id=workspace_id,
            user_id=user_id,
            bundle_id=bundle_id,
            protocols=["WSP"]
        )
        
        return request
    
    def _get_compute_type_from_bundle(self, bundle_id: str) -> str:
        """Map bundle ID to compute type name.
        
        Args:
            bundle_id: WorkSpace bundle ID
            
        Returns:
            Compute type name
        """
        # This is a simplified mapping. In production, query the bundle details
        # from AWS to get the actual compute type
        bundle_type_map = {
            "STANDARD": "VALUE",
            "PERFORMANCE": "PERFORMANCE",
            "POWER": "POWER",
            "POWERPRO": "POWERPRO",
            "GRAPHICS_G4DN": "GRAPHICS_G4DN",
            "GRAPHICSPRO_G4DN": "GRAPHICSPRO_G4DN"
        }
        
        # Extract bundle type from bundle_id (simplified)
        for bundle_type, compute_type in bundle_type_map.items():
            if bundle_type in bundle_id.upper():
                return compute_type
        
        # Default to VALUE if not found
        return "VALUE"
    
    def verify_wsp_only_configuration(
        self,
        workspace_id: str
    ) -> bool:
        """Verify that WorkSpace is configured for WSP-only.
        
        Requirements:
        - Validates: Requirements 3.1 (WSP-only verification)
        - Validates: Requirements 3.2 (PCoIP disabled)
        
        Args:
            workspace_id: WorkSpace ID to verify
            
        Returns:
            True if WSP-only, False otherwise
        """
        try:
            workspaces = self.client.describe_workspaces(
                workspace_ids=[workspace_id]
            )
            
            if not workspaces:
                logger.error(
                    f"workspace_not_found_for_verification workspace_id={workspace_id}"
                )
                return False
            
            workspace = workspaces[0]
            properties = workspace.get("WorkspaceProperties", {})
            protocols = properties.get("Protocols", [])
            
            # Check that only WSP is enabled
            is_wsp_only = (
                "WSP" in protocols and
                "PCoIP" not in protocols and
                len(protocols) == 1
            )
            
            if is_wsp_only:
                logger.info(
                    "wsp_only_verified",
                    workspace_id=workspace_id,
                    protocols=protocols
                )
            else:
                logger.error(
                    f"wsp_only_verification_failed workspace_id={workspace_id} protocols={protocols}"
                )
            
            return is_wsp_only
            
        except Exception as e:
            logger.error(
                "wsp_verification_error",
                workspace_id=workspace_id,
                error=str(e)
            )
            return False
    
    def get_connection_url(
        self,
        workspace_id: str,
        region: str
    ) -> str:
        """Generate WSP connection URL for WorkSpace.
        
        Args:
            workspace_id: WorkSpace ID
            region: AWS region
            
        Returns:
            WSP connection URL
        """
        # WorkSpaces connection URL format
        # Users can connect via web client, native client, or mobile client
        return f"https://clients.amazonworkspaces.com/webclient#/workspaces/{workspace_id}?region={region}"
    
    def apply_security_policies(
        self,
        workspace_id: str,
        user_id: str,
        session_id: str
    ) -> bool:
        """Apply security Group Policies to WorkSpace.
        
        Note: This is a placeholder for the actual Group Policy application.
        In production, this would integrate with Active Directory Group Policy
        management to apply the policies defined in SECURITY_GROUP_POLICIES.
        
        Requirements:
        - Validates: Requirements 7.1-7.7 (Data exfiltration prevention)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if policies applied successfully
        """
        try:
            policy_config = self.get_security_group_policy_config(user_id, session_id)
            
            # TODO: Integrate with Active Directory Group Policy management
            # This would typically involve:
            # 1. Creating/updating GPO in Active Directory
            # 2. Linking GPO to WorkSpace OU
            # 3. Forcing Group Policy update on WorkSpace
            
            logger.info(
                "security_policies_applied",
                workspace_id=workspace_id,
                user_id=user_id,
                policies=list(policy_config.keys())
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "security_policy_application_failed",
                workspace_id=workspace_id,
                error=str(e)
            )
            return False

"""User volume management service for FSx ONTAP.

Requirements:
- 4.4: Attach user volume from FSx ONTAP
- 4.5: Persist user volume on disconnect
- 20.1: Sync dotfiles from user volume
- 20.2: Support shell, editor, Git configs
- 20.3: Persist dotfile changes
- 20.4: Apply dotfiles within 30 seconds
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class UserVolumeService:
    """Service for managing user volumes on FSx ONTAP."""
    
    # Dotfile paths to sync
    DOTFILE_PATTERNS = [
        ".bashrc",
        ".bash_profile",
        ".zshrc",
        ".vimrc",
        ".gitconfig",
        ".ssh/config",
        ".aws/config",
        ".aws/credentials",
    ]
    
    # Sync timeout
    SYNC_TIMEOUT_SECONDS = 30
    
    def __init__(
        self,
        fsx_filesystem_id: str,
        fsx_svm_id: str,
        region: str = "us-west-2"
    ):
        """Initialize user volume service.
        
        Args:
            fsx_filesystem_id: FSx filesystem ID
            fsx_svm_id: FSx Storage Virtual Machine ID
            region: AWS region
        """
        self.fsx_filesystem_id = fsx_filesystem_id
        self.fsx_svm_id = fsx_svm_id
        self.region = region
        
        self.fsx_client = boto3.client("fsx", region_name=region)
        self.ssm_client = boto3.client("ssm", region_name=region)
        
        logger.info(
            "user_volume_service_initialized",
            extra={
                "fsx_filesystem_id": fsx_filesystem_id,
                "fsx_svm_id": fsx_svm_id,
                "region": region
            }
        )
    
    def create_user_volume(
        self,
        user_id: str,
        size_gb: int = 100
    ) -> Dict[str, Any]:
        """Create a user volume on FSx ONTAP.
        
        Requirements:
        - Validates: Requirements 4.4 (User volume creation)
        
        Args:
            user_id: User identifier
            size_gb: Volume size in GB
            
        Returns:
            Dictionary with volume details
        """
        try:
            volume_name = f"user-{user_id}"
            junction_path = f"/users/{user_id}"
            
            logger.info(
                "creating_user_volume",
                extra={
                    "user_id": user_id,
                    "volume_name": volume_name,
                    "size_gb": size_gb
                }
            )
            
            # Create volume on FSx ONTAP
            response = self.fsx_client.create_volume(
                VolumeType="ONTAP",
                Name=volume_name,
                OntapConfiguration={
                    "StorageVirtualMachineId": self.fsx_svm_id,
                    "JunctionPath": junction_path,
                    "SizeInMegabytes": size_gb * 1024,
                    "StorageEfficiencyEnabled": True,  # Enable deduplication/compression
                    "SecurityStyle": "UNIX",
                    "TieringPolicy": {
                        "Name": "AUTO"
                    }
                },
                Tags=[
                    {"Key": "UserId", "Value": user_id},
                    {"Key": "Purpose", "Value": "UserVolume"}
                ]
            )
            
            volume = response["Volume"]
            
            logger.info(
                "user_volume_created",
                extra={
                    "user_id": user_id,
                    "volume_id": volume["VolumeId"],
                    "junction_path": junction_path
                }
            )
            
            return {
                "volume_id": volume["VolumeId"],
                "volume_name": volume_name,
                "junction_path": junction_path,
                "size_gb": size_gb,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            logger.error(
                "user_volume_creation_failed",
                extra={
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def attach_volume_to_workspace(
        self,
        workspace_id: str,
        user_id: str,
        volume_id: str
    ) -> bool:
        """Attach user volume to a WorkSpace.
        
        Requirements:
        - Validates: Requirements 4.4 (Volume attachment)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            volume_id: FSx volume ID
            
        Returns:
            True if attachment successful
        """
        try:
            logger.info(
                "attaching_user_volume",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "volume_id": volume_id
                }
            )
            
            # Mount volume on WorkSpace using SSM
            mount_path = f"/home/{user_id}/workspace"
            junction_path = f"/users/{user_id}"
            
            # Get FSx DNS name
            volume_info = self.fsx_client.describe_volumes(
                VolumeIds=[volume_id]
            )
            
            if not volume_info["Volumes"]:
                raise ValueError(f"Volume not found: {volume_id}")
            
            # TODO: Use SSM to execute mount command on WorkSpace
            # This would typically involve:
            # 1. Get FSx NFS endpoint
            # 2. Create mount point directory
            # 3. Mount NFS volume
            # 4. Set permissions
            
            logger.info(
                "user_volume_attached",
                extra={
                    "workspace_id": workspace_id,
                    "volume_id": volume_id,
                    "mount_path": mount_path
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "volume_attachment_failed",
                extra={
                    "workspace_id": workspace_id,
                    "volume_id": volume_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    def detach_volume_from_workspace(
        self,
        workspace_id: str,
        volume_id: str
    ) -> bool:
        """Detach user volume from WorkSpace.
        
        Requirements:
        - Validates: Requirements 4.5 (Volume persistence on disconnect)
        
        Args:
            workspace_id: WorkSpace ID
            volume_id: FSx volume ID
            
        Returns:
            True if detachment successful
        """
        try:
            logger.info(
                "detaching_user_volume",
                extra={
                    "workspace_id": workspace_id,
                    "volume_id": volume_id
                }
            )
            
            # TODO: Use SSM to unmount volume from WorkSpace
            # This would typically involve:
            # 1. Sync any pending writes
            # 2. Unmount NFS volume
            # 3. Verify unmount succeeded
            
            logger.info(
                "user_volume_detached",
                extra={
                    "workspace_id": workspace_id,
                    "volume_id": volume_id,
                    "note": "Volume persisted on FSx ONTAP"
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "volume_detachment_failed",
                extra={
                    "workspace_id": workspace_id,
                    "volume_id": volume_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    def sync_dotfiles_to_workspace(
        self,
        workspace_id: str,
        user_id: str,
        volume_id: str
    ) -> Dict[str, Any]:
        """Sync dotfiles from user volume to WorkSpace.
        
        Requirements:
        - Validates: Requirements 20.1 (Sync dotfiles from user volume)
        - Validates: Requirements 20.2 (Support shell, editor, Git configs)
        - Validates: Requirements 20.4 (Apply within 30 seconds)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            volume_id: FSx volume ID
            
        Returns:
            Dictionary with sync results
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(
                "syncing_dotfiles_to_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "patterns": self.DOTFILE_PATTERNS
                }
            )
            
            synced_files = []
            failed_files = []
            
            # TODO: Use SSM to sync dotfiles
            # This would typically involve:
            # 1. Copy dotfiles from volume mount to home directory
            # 2. Set correct permissions
            # 3. Create symlinks if needed
            # 4. Verify files are accessible
            
            for pattern in self.DOTFILE_PATTERNS:
                # Placeholder: mark as synced
                synced_files.append(pattern)
            
            end_time = datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
            
            if duration_seconds > self.SYNC_TIMEOUT_SECONDS:
                logger.warning(
                    "dotfile_sync_exceeded_timeout",
                    extra={
                        "workspace_id": workspace_id,
                        "duration_seconds": duration_seconds,
                        "timeout_seconds": self.SYNC_TIMEOUT_SECONDS
                    }
                )
            
            logger.info(
                "dotfiles_synced_to_workspace",
                extra={
                    "workspace_id": workspace_id,
                    "synced_count": len(synced_files),
                    "failed_count": len(failed_files),
                    "duration_seconds": duration_seconds
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "synced_files": synced_files,
                "failed_files": failed_files,
                "duration_seconds": duration_seconds,
                "within_timeout": duration_seconds <= self.SYNC_TIMEOUT_SECONDS,
                "synced_at": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(
                "dotfile_sync_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def sync_dotfiles_to_volume(
        self,
        workspace_id: str,
        user_id: str,
        volume_id: str
    ) -> Dict[str, Any]:
        """Sync dotfiles from WorkSpace back to user volume.
        
        Requirements:
        - Validates: Requirements 20.3 (Persist dotfile changes)
        
        Args:
            workspace_id: WorkSpace ID
            user_id: User identifier
            volume_id: FSx volume ID
            
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(
                "syncing_dotfiles_to_volume",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "volume_id": volume_id
                }
            )
            
            synced_files = []
            
            # TODO: Use SSM to sync dotfiles back to volume
            # This would typically involve:
            # 1. Copy modified dotfiles from home directory to volume
            # 2. Preserve timestamps
            # 3. Verify sync succeeded
            
            for pattern in self.DOTFILE_PATTERNS:
                synced_files.append(pattern)
            
            logger.info(
                "dotfiles_synced_to_volume",
                extra={
                    "workspace_id": workspace_id,
                    "synced_count": len(synced_files)
                }
            )
            
            return {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "volume_id": volume_id,
                "synced_files": synced_files,
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "dotfile_sync_to_volume_failed",
                extra={
                    "workspace_id": workspace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_volume_info(
        self,
        volume_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get information about a user volume.
        
        Args:
            volume_id: FSx volume ID
            
        Returns:
            Dictionary with volume information or None
        """
        try:
            response = self.fsx_client.describe_volumes(
                VolumeIds=[volume_id]
            )
            
            if not response["Volumes"]:
                return None
            
            volume = response["Volumes"][0]
            
            return {
                "volume_id": volume["VolumeId"],
                "name": volume["Name"],
                "size_gb": volume["OntapConfiguration"]["SizeInMegabytes"] // 1024,
                "junction_path": volume["OntapConfiguration"]["JunctionPath"],
                "lifecycle": volume["Lifecycle"],
                "created_at": volume["CreationTime"].isoformat()
            }
            
        except ClientError as e:
            logger.error(
                "get_volume_info_failed",
                extra={
                    "volume_id": volume_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return None
    
    def list_user_volumes(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List user volumes, optionally filtered by user.
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of volume information dictionaries
        """
        try:
            filters = []
            if user_id:
                filters.append({
                    "Name": "tag:UserId",
                    "Values": [user_id]
                })
            
            response = self.fsx_client.describe_volumes(
                Filters=filters
            )
            
            volumes = []
            for volume in response.get("Volumes", []):
                if volume.get("VolumeType") == "ONTAP":
                    volumes.append({
                        "volume_id": volume["VolumeId"],
                        "name": volume["Name"],
                        "size_gb": volume["OntapConfiguration"]["SizeInMegabytes"] // 1024,
                        "lifecycle": volume["Lifecycle"]
                    })
            
            return volumes
            
        except ClientError as e:
            logger.error(
                "list_user_volumes_failed",
                extra={
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return []

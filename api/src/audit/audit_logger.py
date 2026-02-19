"""Audit logging service for RobCo Forge.

Requirements:
- 10.1: Comprehensive audit logging for all actions
- 10.2: Audit log completeness (timestamp, user, action, resource, result, IP)
- 10.3: Tamper-evident storage
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging
import hashlib
import json
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog
from ..database import SessionLocal

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for creating audit log entries.
    
    Requirements:
    - 10.1: Capture all API requests
    - 10.2: Extract user identity, action, resource, result
    - 10.3: Store in tamper-evident format
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self._previous_hash: Optional[str] = None
    
    def _calculate_hash(self, log_entry: Dict[str, Any]) -> str:
        """Calculate tamper-evident hash for log entry.
        
        Creates a hash chain where each entry includes the hash of the previous entry.
        This makes it detectable if any entry is modified or deleted.
        
        Validates: Requirements 10.3
        
        Args:
            log_entry: Log entry data
            
        Returns:
            SHA-256 hash of the entry
        """
        # Create deterministic string representation
        hash_data = {
            "timestamp": log_entry["timestamp"].isoformat() if isinstance(log_entry["timestamp"], datetime) else log_entry["timestamp"],
            "user_id": log_entry["user_id"],
            "action": log_entry["action"],
            "resource_type": log_entry["resource_type"],
            "resource_id": log_entry.get("resource_id"),
            "result": log_entry["result"],
            "previous_hash": self._previous_hash or "genesis",
        }
        
        # Create JSON string with sorted keys for consistency
        hash_string = json.dumps(hash_data, sort_keys=True)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        result: str,
        resource_id: Optional[str] = None,
        error_message: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        interface: Optional[str] = None,
        workspace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> AuditLog:
        """Create an audit log entry.
        
        Validates: Requirements 10.1, 10.2, 10.3
        
        Args:
            user_id: User identifier
            action: Action performed (e.g., "workspace.create", "blueprint.update")
            resource_type: Type of resource (e.g., "workspace", "blueprint")
            result: Result of action ("SUCCESS", "FAILURE", "DENIED")
            resource_id: Optional resource identifier
            error_message: Optional error message for failures
            source_ip: Source IP address
            user_agent: User agent string
            interface: Interface used (PORTAL, CLI, LUCY)
            workspace_id: Optional workspace ID for workspace-related actions
            metadata: Optional additional metadata
            db: Database session (creates new if not provided)
            
        Returns:
            Created audit log entry
        """
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True
        
        try:
            timestamp = datetime.utcnow()
            
            # Prepare log entry data
            log_data = {
                "timestamp": timestamp,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "result": result,
            }
            
            # Calculate tamper-evident hash
            entry_hash = self._calculate_hash(log_data)
            
            # Create audit log entry
            audit_entry = AuditLog(
                id=f"audit-{uuid4().hex[:16]}",
                timestamp=timestamp,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                error_message=error_message,
                source_ip=source_ip,
                user_agent=user_agent,
                interface=interface,
                workspace_id=workspace_id,
                metadata=metadata or {},
            )
            
            # Store hash in metadata for verification
            audit_entry.metadata["_hash"] = entry_hash
            audit_entry.metadata["_previous_hash"] = self._previous_hash or "genesis"
            
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            
            # Update previous hash for next entry
            self._previous_hash = entry_hash
            
            logger.info(
                "audit_log_created",
                audit_id=audit_entry.id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                result=result,
            )
            
            return audit_entry
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            if should_close_db:
                db.rollback()
            raise
        finally:
            if should_close_db:
                db.close()
    
    def verify_chain(self, db: Session, limit: int = 100) -> Dict[str, Any]:
        """Verify the integrity of the audit log chain.
        
        Checks that the hash chain is intact and no entries have been tampered with.
        
        Validates: Requirements 10.3
        
        Args:
            db: Database session
            limit: Number of recent entries to verify
            
        Returns:
            Verification result with status and details
        """
        try:
            # Get recent audit logs ordered by timestamp
            logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
            logs.reverse()  # Process in chronological order
            
            if not logs:
                return {
                    "status": "valid",
                    "message": "No audit logs to verify",
                    "verified_count": 0,
                }
            
            previous_hash = None
            verified_count = 0
            tampered_entries = []
            
            for log in logs:
                # Get stored hash from metadata
                stored_hash = log.metadata.get("_hash")
                stored_previous_hash = log.metadata.get("_previous_hash")
                
                if not stored_hash:
                    tampered_entries.append({
                        "audit_id": log.id,
                        "reason": "Missing hash in metadata",
                    })
                    continue
                
                # Verify previous hash matches
                if previous_hash is not None and stored_previous_hash != previous_hash:
                    tampered_entries.append({
                        "audit_id": log.id,
                        "reason": f"Previous hash mismatch: expected {previous_hash}, got {stored_previous_hash}",
                    })
                
                # Recalculate hash and verify
                log_data = {
                    "timestamp": log.timestamp,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "result": log.result,
                }
                
                calculated_hash = self._calculate_hash(log_data)
                
                if calculated_hash != stored_hash:
                    tampered_entries.append({
                        "audit_id": log.id,
                        "reason": f"Hash mismatch: expected {stored_hash}, calculated {calculated_hash}",
                    })
                else:
                    verified_count += 1
                
                previous_hash = stored_hash
            
            if tampered_entries:
                return {
                    "status": "tampered",
                    "message": f"Found {len(tampered_entries)} tampered entries",
                    "verified_count": verified_count,
                    "total_count": len(logs),
                    "tampered_entries": tampered_entries,
                }
            else:
                return {
                    "status": "valid",
                    "message": "All audit logs verified successfully",
                    "verified_count": verified_count,
                    "total_count": len(logs),
                }
                
        except Exception as e:
            logger.error(f"Failed to verify audit chain: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Verification failed: {str(e)}",
            }


# Global audit logger instance
_audit_logger = AuditLogger()


def audit_log(
    user_id: str,
    action: str,
    resource_type: str,
    result: str,
    **kwargs
) -> AuditLog:
    """Convenience function for creating audit logs.
    
    Args:
        user_id: User identifier
        action: Action performed
        resource_type: Type of resource
        result: Result of action
        **kwargs: Additional audit log fields
        
    Returns:
        Created audit log entry
    """
    return _audit_logger.log_action(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        result=result,
        **kwargs
    )


def verify_audit_chain(db: Session, limit: int = 100) -> Dict[str, Any]:
    """Verify the integrity of the audit log chain.
    
    Args:
        db: Database session
        limit: Number of recent entries to verify
        
    Returns:
        Verification result
    """
    return _audit_logger.verify_chain(db, limit)

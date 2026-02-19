"""AWS WorkSpaces API client with retry logic and circuit breaker.

Requirements:
- 1.1: Self-service WorkSpace provisioning
- 1.2: Support for WorkSpaces Personal and WorkSpaces Applications
- 1.3: Bundle type selection
- 1.4: Operating system selection
"""

import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation for AWS API calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 30,
        success_threshold: int = 2
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before trying again
            success_threshold: Successes needed in half-open to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("circuit_breaker_half_open", service="workspaces")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry after {self.timeout_seconds} seconds."
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout_seconds)
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info("circuit_breaker_closed", service="workspaces")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                "circuit_breaker_opened",
                service="workspaces",
                failure_count=self.failure_count
            )


class WorkSpacesClient:
    """AWS WorkSpaces API client with retry logic and circuit breaker.
    
    Implements exponential backoff retry and circuit breaker pattern
    for resilient AWS API interactions.
    """
    
    # Retry configuration
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1.0  # seconds
    MAX_BACKOFF = 16.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    
    def __init__(self, region: str = "us-west-2"):
        """Initialize WorkSpaces client.
        
        Args:
            region: AWS region for WorkSpaces operations
        """
        self.region = region
        self.client = boto3.client("workspaces", region_name=region)
        self.circuit_breaker = CircuitBreaker()
        
        logger.info("workspaces_client_initialized", region=region)
    
    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries exhausted
        """
        backoff = self.INITIAL_BACKOFF
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return self.circuit_breaker.call(func, *args, **kwargs)
            except (ClientError, BotoCoreError) as e:
                last_exception = e
                error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
                
                # Don't retry on certain errors
                if error_code in ["InvalidParameterValuesException", "ResourceNotFoundException"]:
                    logger.error(
                        "workspaces_api_non_retryable_error",
                        error_code=error_code,
                        attempt=attempt + 1
                    )
                    raise
                
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"workspaces_api_retry attempt={attempt + 1} max_retries={self.MAX_RETRIES} "
                        f"backoff_seconds={backoff} error_code={error_code}"
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * self.BACKOFF_MULTIPLIER, self.MAX_BACKOFF)
                else:
                    logger.error(
                        "workspaces_api_retries_exhausted",
                        attempts=self.MAX_RETRIES,
                        error_code=error_code
                    )
        
        raise last_exception
    
    def create_workspaces(
        self,
        workspaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create one or more WorkSpaces.
        
        Requirements:
        - Validates: Requirements 1.1 (Provisioning within 5 minutes)
        - Validates: Requirements 1.3 (Bundle type selection)
        - Validates: Requirements 1.4 (Operating system selection)
        
        Args:
            workspaces: List of WorkSpace specifications
            
        Returns:
            Response from AWS WorkSpaces API
            
        Raises:
            ClientError: If AWS API call fails
        """
        def _create():
            return self.client.create_workspaces(Workspaces=workspaces)
        
        logger.info(
            "creating_workspaces",
            count=len(workspaces),
            region=self.region
        )
        
        response = self._retry_with_backoff(_create)
        
        logger.info(
            "workspaces_created",
            pending_count=len(response.get("PendingRequests", [])),
            failed_count=len(response.get("FailedRequests", []))
        )
        
        return response
    
    def describe_workspaces(
        self,
        workspace_ids: Optional[List[str]] = None,
        directory_id: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Describe WorkSpaces.
        
        Args:
            workspace_ids: Optional list of WorkSpace IDs to describe
            directory_id: Optional directory ID filter
            user_name: Optional user name filter
            
        Returns:
            List of WorkSpace descriptions
        """
        def _describe():
            params = {}
            if workspace_ids:
                params["WorkspaceIds"] = workspace_ids
            if directory_id:
                params["DirectoryId"] = directory_id
            if user_name:
                params["UserName"] = user_name
            
            return self.client.describe_workspaces(**params)
        
        response = self._retry_with_backoff(_describe)
        return response.get("Workspaces", [])
    
    def start_workspaces(self, workspace_ids: List[str]) -> Dict[str, Any]:
        """Start one or more WorkSpaces.
        
        Args:
            workspace_ids: List of WorkSpace IDs to start
            
        Returns:
            Response from AWS WorkSpaces API
        """
        def _start():
            requests = [{"WorkspaceId": ws_id} for ws_id in workspace_ids]
            return self.client.start_workspaces(StartWorkspaceRequests=requests)
        
        logger.info("starting_workspaces", workspace_ids=workspace_ids)
        response = self._retry_with_backoff(_start)
        
        logger.info(
            "workspaces_start_initiated",
            failed_count=len(response.get("FailedRequests", []))
        )
        
        return response
    
    def stop_workspaces(self, workspace_ids: List[str]) -> Dict[str, Any]:
        """Stop one or more WorkSpaces.
        
        Args:
            workspace_ids: List of WorkSpace IDs to stop
            
        Returns:
            Response from AWS WorkSpaces API
        """
        def _stop():
            requests = [{"WorkspaceId": ws_id} for ws_id in workspace_ids]
            return self.client.stop_workspaces(StopWorkspaceRequests=requests)
        
        logger.info("stopping_workspaces", workspace_ids=workspace_ids)
        response = self._retry_with_backoff(_stop)
        
        logger.info(
            "workspaces_stop_initiated",
            failed_count=len(response.get("FailedRequests", []))
        )
        
        return response
    
    def terminate_workspaces(self, workspace_ids: List[str]) -> Dict[str, Any]:
        """Terminate one or more WorkSpaces.
        
        Args:
            workspace_ids: List of WorkSpace IDs to terminate
            
        Returns:
            Response from AWS WorkSpaces API
        """
        def _terminate():
            requests = [{"WorkspaceId": ws_id} for ws_id in workspace_ids]
            return self.client.terminate_workspaces(TerminateWorkspaceRequests=requests)
        
        logger.info("terminating_workspaces", workspace_ids=workspace_ids)
        response = self._retry_with_backoff(_terminate)
        
        logger.info(
            "workspaces_terminated",
            failed_count=len(response.get("FailedRequests", []))
        )
        
        return response
    
    def modify_workspace_properties(
        self,
        workspace_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify WorkSpace properties.
        
        Args:
            workspace_id: WorkSpace ID
            properties: Properties to modify
            
        Returns:
            Response from AWS WorkSpaces API
        """
        def _modify():
            return self.client.modify_workspace_properties(
                WorkspaceId=workspace_id,
                WorkspaceProperties=properties
            )
        
        logger.info(
            "modifying_workspace_properties",
            workspace_id=workspace_id,
            properties=properties
        )
        
        return self._retry_with_backoff(_modify)
    
    def describe_workspace_bundles(
        self,
        bundle_ids: Optional[List[str]] = None,
        owner: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Describe available WorkSpace bundles.
        
        Args:
            bundle_ids: Optional list of bundle IDs
            owner: Optional owner filter (AMAZON or account ID)
            
        Returns:
            List of bundle descriptions
        """
        def _describe():
            params = {}
            if bundle_ids:
                params["BundleIds"] = bundle_ids
            if owner:
                params["Owner"] = owner
            
            return self.client.describe_workspace_bundles(**params)
        
        response = self._retry_with_backoff(_describe)
        return response.get("Bundles", [])
    
    def describe_workspace_directories(
        self,
        directory_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Describe WorkSpace directories.
        
        Args:
            directory_ids: Optional list of directory IDs
            
        Returns:
            List of directory descriptions
        """
        def _describe():
            params = {}
            if directory_ids:
                params["DirectoryIds"] = directory_ids
            
            return self.client.describe_workspace_directories(**params)
        
        response = self._retry_with_backoff(_describe)
        return response.get("Directories", [])

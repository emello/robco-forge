"""Tests for provisioning service.

Tests the WorkSpaces client, region selector, and workspace configurator.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.provisioning.workspaces_client import WorkSpacesClient, CircuitBreaker, CircuitState
from src.provisioning.region_selector import RegionSelector
from src.provisioning.workspace_configurator import WorkSpaceConfigurator


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows calls."""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=10)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=10)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
    
    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects calls when open."""
        cb = CircuitBreaker(failure_threshold=1, timeout_seconds=10)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        with pytest.raises(Exception):
            cb.call(failing_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Next call should be rejected
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(failing_func)


class TestWorkSpacesClient:
    """Test WorkSpaces API client."""
    
    @patch('src.provisioning.workspaces_client.boto3.client')
    def test_create_workspaces_success(self, mock_boto_client):
        """Test successful WorkSpace creation."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        mock_client.create_workspaces.return_value = {
            "PendingRequests": [{"WorkspaceId": "ws-test123"}],
            "FailedRequests": []
        }
        
        client = WorkSpacesClient(region="us-west-2")
        workspaces = [{"DirectoryId": "d-123", "UserName": "test"}]
        
        response = client.create_workspaces(workspaces)
        
        assert len(response["PendingRequests"]) == 1
        assert len(response["FailedRequests"]) == 0
        mock_client.create_workspaces.assert_called_once()
    
    @patch('src.provisioning.workspaces_client.boto3.client')
    def test_create_workspaces_with_retry(self, mock_boto_client):
        """Test WorkSpace creation with retry on transient error."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # First call fails, second succeeds
        mock_client.create_workspaces.side_effect = [
            ClientError(
                {"Error": {"Code": "InternalServerError"}},
                "create_workspaces"
            ),
            {
                "PendingRequests": [{"WorkspaceId": "ws-test123"}],
                "FailedRequests": []
            }
        ]
        
        client = WorkSpacesClient(region="us-west-2")
        workspaces = [{"DirectoryId": "d-123", "UserName": "test"}]
        
        response = client.create_workspaces(workspaces)
        
        assert len(response["PendingRequests"]) == 1
        assert mock_client.create_workspaces.call_count == 2
    
    @patch('src.provisioning.workspaces_client.boto3.client')
    def test_describe_workspaces(self, mock_boto_client):
        """Test describing WorkSpaces."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        mock_client.describe_workspaces.return_value = {
            "Workspaces": [
                {"WorkspaceId": "ws-123", "State": "AVAILABLE"},
                {"WorkspaceId": "ws-456", "State": "STOPPED"}
            ]
        }
        
        client = WorkSpacesClient(region="us-west-2")
        workspaces = client.describe_workspaces(workspace_ids=["ws-123", "ws-456"])
        
        assert len(workspaces) == 2
        assert workspaces[0]["WorkspaceId"] == "ws-123"
        assert workspaces[1]["State"] == "STOPPED"


class TestRegionSelector:
    """Test region selection logic."""
    
    def test_calculate_distance(self):
        """Test distance calculation between two points."""
        selector = RegionSelector()
        
        # Distance from San Francisco to New York (approx 4130 km)
        sf_lat, sf_lon = 37.77, -122.42
        ny_lat, ny_lon = 40.71, -74.01
        
        distance = selector.calculate_distance(sf_lat, sf_lon, ny_lat, ny_lon)
        
        # Allow 10% margin of error
        assert 3700 < distance < 4500
    
    def test_select_optimal_region_west_coast(self):
        """Test region selection for West Coast US location."""
        selector = RegionSelector()
        
        # San Francisco coordinates
        sf_location = (37.77, -122.42)
        
        region = selector.select_optimal_region(sf_location)
        
        # Should select us-west-2 (Oregon) as closest
        assert region == "us-west-2"
    
    def test_select_optimal_region_east_coast(self):
        """Test region selection for East Coast US location."""
        selector = RegionSelector()
        
        # New York coordinates
        ny_location = (40.71, -74.01)
        
        region = selector.select_optimal_region(ny_location)
        
        # Should select us-east-1 (Virginia) as closest
        assert region == "us-east-1"
    
    def test_select_optimal_region_europe(self):
        """Test region selection for European location."""
        selector = RegionSelector()
        
        # London coordinates
        london_location = (51.51, -0.13)
        
        region = selector.select_optimal_region(london_location)
        
        # Should select eu-west-2 (London) as closest
        assert region == "eu-west-2"
    
    @patch('src.provisioning.region_selector.requests.get')
    def test_detect_location_from_ip_success(self, mock_get):
        """Test successful IP geolocation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "lat": 37.77,
            "lon": -122.42,
            "city": "San Francisco",
            "country": "United States"
        }
        mock_get.return_value = mock_response
        
        selector = RegionSelector()
        location = selector.detect_location_from_ip("8.8.8.8")
        
        assert location is not None
        assert location[0] == 37.77
        assert location[1] == -122.42
    
    @patch('src.provisioning.region_selector.requests.get')
    def test_detect_location_from_ip_failure(self, mock_get):
        """Test IP geolocation failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        selector = RegionSelector()
        location = selector.detect_location_from_ip("8.8.8.8")
        
        assert location is None
    
    @patch('src.provisioning.region_selector.requests.get')
    def test_select_region_for_user_with_fallback(self, mock_get):
        """Test region selection falls back to default on error."""
        mock_get.side_effect = Exception("Network error")
        
        selector = RegionSelector(default_region="us-west-2")
        region = selector.select_region_for_user("8.8.8.8")
        
        assert region == "us-west-2"


class TestWorkSpaceConfigurator:
    """Test WorkSpace configuration."""
    
    def test_get_wsp_only_properties(self):
        """Test WSP-only properties generation."""
        mock_client = Mock()
        configurator = WorkSpaceConfigurator(mock_client)
        
        properties = configurator.get_wsp_only_properties()
        
        assert "Protocols" in properties
        assert properties["Protocols"] == ["WSP"]
        assert "PCoIP" not in properties["Protocols"]
    
    def test_get_security_group_policy_config(self):
        """Test security Group Policy configuration."""
        mock_client = Mock()
        configurator = WorkSpaceConfigurator(mock_client)
        
        config = configurator.get_security_group_policy_config(
            user_id="user123",
            session_id="session456"
        )
        
        # Verify all data exfiltration vectors are disabled
        assert config["clipboard_operations"] is False
        assert config["usb_device_redirection"] is False
        assert config["drive_redirection"] is False
        assert config["file_transfer"] is False
        assert config["printing"] is False
        
        # Verify watermark is enabled
        assert config["screen_watermark"]["enabled"] is True
        assert "user123" in config["screen_watermark"]["text"]
        assert "session456" in config["screen_watermark"]["text"]
    
    def test_build_workspace_request(self):
        """Test WorkSpace creation request building."""
        mock_client = Mock()
        configurator = WorkSpaceConfigurator(mock_client)
        
        request = configurator.build_workspace_request(
            directory_id="d-123",
            user_name="testuser",
            bundle_id="wsb-performance",
            user_id="user123",
            workspace_id="ws-abc",
            tags=[{"Key": "Project", "Value": "Test"}]
        )
        
        assert request["DirectoryId"] == "d-123"
        assert request["UserName"] == "testuser"
        assert request["BundleId"] == "wsb-performance"
        
        # Verify WSP-only protocol
        assert request["WorkspaceProperties"]["Protocols"] == ["WSP"]
        
        # Verify tags include workspace and user IDs
        tag_keys = [tag["Key"] for tag in request["Tags"]]
        assert "WorkspaceId" in tag_keys
        assert "UserId" in tag_keys
    
    def test_verify_wsp_only_configuration_success(self):
        """Test WSP-only verification succeeds."""
        mock_client = Mock()
        mock_client.describe_workspaces.return_value = [
            {
                "WorkspaceId": "ws-123",
                "WorkspaceProperties": {
                    "Protocols": ["WSP"]
                }
            }
        ]
        
        configurator = WorkSpaceConfigurator(mock_client)
        result = configurator.verify_wsp_only_configuration("ws-123")
        
        assert result is True
    
    def test_verify_wsp_only_configuration_failure(self):
        """Test WSP-only verification fails when PCoIP enabled."""
        mock_client = Mock()
        mock_client.describe_workspaces.return_value = [
            {
                "WorkspaceId": "ws-123",
                "WorkspaceProperties": {
                    "Protocols": ["WSP", "PCoIP"]
                }
            }
        ]
        
        configurator = WorkSpaceConfigurator(mock_client)
        result = configurator.verify_wsp_only_configuration("ws-123")
        
        assert result is False
    
    def test_get_connection_url(self):
        """Test connection URL generation."""
        mock_client = Mock()
        configurator = WorkSpaceConfigurator(mock_client)
        
        url = configurator.get_connection_url("ws-123", "us-west-2")
        
        assert "ws-123" in url
        assert "us-west-2" in url
        assert url.startswith("https://")



class TestDomainJoinService:
    """Test Active Directory domain join service."""
    
    def test_join_workspace_to_domain_success(self):
        """Test successful domain join on first attempt."""
        from src.provisioning.domain_join_service import DomainJoinService, DomainJoinStatus
        
        mock_client = Mock()
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local",
            domain_ou="OU=WorkSpaces,OU=Computers,DC=robco,DC=local"
        )
        
        result = service.join_workspace_to_domain(
            workspace_id="ws-123",
            user_name="jdoe",
            directory_id="d-123"
        )
        
        assert result["status"] == DomainJoinStatus.JOINED.value
        assert result["workspace_id"] == "ws-123"
        assert result["domain_name"] == "robco.local"
        assert result["attempts"] == 1
        assert "joined_at" in result
    
    def test_join_workspace_to_domain_with_retry(self):
        """Test domain join succeeds after retry."""
        from src.provisioning.domain_join_service import DomainJoinService, DomainJoinStatus
        
        mock_client = Mock()
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        # Mock _perform_domain_join to fail once, then succeed
        call_count = 0
        def mock_perform_join(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"success": False, "error": "Temporary failure"}
            return {"success": True, "workspace_id": "ws-123", "domain_name": "robco.local"}
        
        service._perform_domain_join = mock_perform_join
        
        result = service.join_workspace_to_domain(
            workspace_id="ws-123",
            user_name="jdoe",
            directory_id="d-123"
        )
        
        assert result["status"] == DomainJoinStatus.JOINED.value
        assert result["attempts"] == 2
        assert call_count == 2
    
    def test_join_workspace_to_domain_max_retries_exceeded(self):
        """Test domain join fails after max retries."""
        from src.provisioning.domain_join_service import DomainJoinService, DomainJoinStatus
        
        mock_client = Mock()
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        # Mock _perform_domain_join to always fail
        service._perform_domain_join = Mock(
            return_value={"success": False, "error": "Persistent failure"}
        )
        
        result = service.join_workspace_to_domain(
            workspace_id="ws-123",
            user_name="jdoe",
            directory_id="d-123"
        )
        
        assert result["status"] == DomainJoinStatus.FAILED.value
        assert result["attempts"] == 3
        assert "error" in result
        assert "failed_at" in result
    
    def test_verify_domain_join_success(self):
        """Test domain join verification succeeds."""
        from src.provisioning.domain_join_service import DomainJoinService
        
        mock_client = Mock()
        mock_client.describe_workspaces.return_value = [
            {
                "WorkspaceId": "ws-123",
                "DirectoryId": "d-123",
                "State": "AVAILABLE"
            }
        ]
        
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        result = service.verify_domain_join("ws-123")
        
        assert result is True
        mock_client.describe_workspaces.assert_called_once_with(workspace_ids=["ws-123"])
    
    def test_verify_domain_join_no_directory(self):
        """Test domain join verification fails when no directory."""
        from src.provisioning.domain_join_service import DomainJoinService
        
        mock_client = Mock()
        mock_client.describe_workspaces.return_value = [
            {
                "WorkspaceId": "ws-123",
                "State": "AVAILABLE"
                # No DirectoryId
            }
        ]
        
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        result = service.verify_domain_join("ws-123")
        
        assert result is False
    
    def test_get_domain_join_status(self):
        """Test getting domain join status."""
        from src.provisioning.domain_join_service import DomainJoinService, DomainJoinStatus
        
        mock_client = Mock()
        mock_client.describe_workspaces.return_value = [
            {
                "WorkspaceId": "ws-123",
                "DirectoryId": "d-123"
            }
        ]
        
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        status = service.get_domain_join_status("ws-123")
        
        assert status["workspace_id"] == "ws-123"
        assert status["status"] == DomainJoinStatus.JOINED.value
        assert status["domain_name"] == "robco.local"
        assert "verified_at" in status
    
    def test_apply_group_policies(self):
        """Test applying Group Policies."""
        from src.provisioning.domain_join_service import DomainJoinService
        
        mock_client = Mock()
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        policies = {
            "clipboard": False,
            "usb_redirection": False,
            "printing": False
        }
        
        result = service.apply_group_policies("ws-123", policies)
        
        assert result is True
    
    def test_configure_domain_authentication(self):
        """Test configuring domain authentication."""
        from src.provisioning.domain_join_service import DomainJoinService
        
        mock_client = Mock()
        service = DomainJoinService(
            workspaces_client=mock_client,
            domain_name="robco.local"
        )
        
        result = service.configure_domain_authentication(
            workspace_id="ws-123",
            user_name="jdoe"
        )
        
        assert result is True



class TestUserVolumeService:
    """Test user volume management service."""
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_create_user_volume(self, mock_boto_client):
        """Test creating a user volume."""
        from src.provisioning.user_volume_service import UserVolumeService
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        mock_fsx.create_volume.return_value = {
            "Volume": {
                "VolumeId": "fsvol-123",
                "Name": "user-jdoe",
                "VolumeType": "ONTAP"
            }
        }
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        result = service.create_user_volume(
            user_id="jdoe",
            size_gb=100
        )
        
        assert result["volume_id"] == "fsvol-123"
        assert result["volume_name"] == "user-jdoe"
        assert result["junction_path"] == "/users/jdoe"
        assert result["size_gb"] == 100
        assert result["user_id"] == "jdoe"
        
        mock_fsx.create_volume.assert_called_once()
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_attach_volume_to_workspace(self, mock_boto_client):
        """Test attaching volume to WorkSpace."""
        from src.provisioning.user_volume_service import UserVolumeService
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        mock_fsx.describe_volumes.return_value = {
            "Volumes": [{
                "VolumeId": "fsvol-123",
                "Name": "user-jdoe"
            }]
        }
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        result = service.attach_volume_to_workspace(
            workspace_id="ws-123",
            user_id="jdoe",
            volume_id="fsvol-123"
        )
        
        assert result is True
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_detach_volume_from_workspace(self, mock_boto_client):
        """Test detaching volume from WorkSpace."""
        from src.provisioning.user_volume_service import UserVolumeService
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        result = service.detach_volume_from_workspace(
            workspace_id="ws-123",
            volume_id="fsvol-123"
        )
        
        assert result is True
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_sync_dotfiles_to_workspace(self, mock_boto_client):
        """Test syncing dotfiles to WorkSpace."""
        from src.provisioning.user_volume_service import UserVolumeService
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        result = service.sync_dotfiles_to_workspace(
            workspace_id="ws-123",
            user_id="jdoe",
            volume_id="fsvol-123"
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["user_id"] == "jdoe"
        assert len(result["synced_files"]) > 0
        assert result["within_timeout"] is True
        assert result["duration_seconds"] <= 30
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_sync_dotfiles_to_volume(self, mock_boto_client):
        """Test syncing dotfiles back to volume."""
        from src.provisioning.user_volume_service import UserVolumeService
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        result = service.sync_dotfiles_to_volume(
            workspace_id="ws-123",
            user_id="jdoe",
            volume_id="fsvol-123"
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["user_id"] == "jdoe"
        assert result["volume_id"] == "fsvol-123"
        assert len(result["synced_files"]) > 0
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_get_volume_info(self, mock_boto_client):
        """Test getting volume information."""
        from src.provisioning.user_volume_service import UserVolumeService
        from datetime import datetime
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        mock_fsx.describe_volumes.return_value = {
            "Volumes": [{
                "VolumeId": "fsvol-123",
                "Name": "user-jdoe",
                "VolumeType": "ONTAP",
                "Lifecycle": "AVAILABLE",
                "CreationTime": datetime.utcnow(),
                "OntapConfiguration": {
                    "SizeInMegabytes": 102400,
                    "JunctionPath": "/users/jdoe"
                }
            }]
        }
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        info = service.get_volume_info("fsvol-123")
        
        assert info is not None
        assert info["volume_id"] == "fsvol-123"
        assert info["name"] == "user-jdoe"
        assert info["size_gb"] == 100
        assert info["junction_path"] == "/users/jdoe"
    
    @patch('src.provisioning.user_volume_service.boto3.client')
    def test_list_user_volumes(self, mock_boto_client):
        """Test listing user volumes."""
        from src.provisioning.user_volume_service import UserVolumeService
        
        mock_fsx = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_fsx if service == "fsx" else mock_ssm
        
        mock_fsx.describe_volumes.return_value = {
            "Volumes": [
                {
                    "VolumeId": "fsvol-123",
                    "Name": "user-jdoe",
                    "VolumeType": "ONTAP",
                    "Lifecycle": "AVAILABLE",
                    "OntapConfiguration": {
                        "SizeInMegabytes": 102400
                    }
                },
                {
                    "VolumeId": "fsvol-456",
                    "Name": "user-jsmith",
                    "VolumeType": "ONTAP",
                    "Lifecycle": "AVAILABLE",
                    "OntapConfiguration": {
                        "SizeInMegabytes": 51200
                    }
                }
            ]
        }
        
        service = UserVolumeService(
            fsx_filesystem_id="fs-123",
            fsx_svm_id="svm-123"
        )
        
        volumes = service.list_user_volumes()
        
        assert len(volumes) == 2
        assert volumes[0]["volume_id"] == "fsvol-123"
        assert volumes[0]["size_gb"] == 100
        assert volumes[1]["volume_id"] == "fsvol-456"
        assert volumes[1]["size_gb"] == 50



class TestSecretsService:
    """Test secrets management service."""
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_get_secrets_for_user_with_user_secrets(self, mock_boto_client):
        """Test getting user-specific secrets."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        # Mock list_secrets to return user-specific secret
        mock_secrets.list_secrets.return_value = {
            "SecretList": [{"Name": "user-jdoe-api-key"}]
        }
        
        # Mock get_secret_value
        mock_secrets.get_secret_value.return_value = {
            "SecretString": "secret-value-123"
        }
        
        service = SecretsService(region="us-west-2")
        secrets = service.get_secrets_for_user(
            user_id="jdoe",
            user_roles=["developer"]
        )
        
        assert "user-jdoe-api-key" in secrets
        assert secrets["user-jdoe-api-key"] == "secret-value-123"
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_get_secrets_for_user_with_team_secrets(self, mock_boto_client):
        """Test getting team-specific secrets."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        # Mock list_secrets to return team secret
        mock_secrets.list_secrets.return_value = {
            "SecretList": [{"Name": "team-engineering-db-password"}]
        }
        
        mock_secrets.get_secret_value.return_value = {
            "SecretString": "team-secret-456"
        }
        
        service = SecretsService(region="us-west-2")
        secrets = service.get_secrets_for_user(
            user_id="jdoe",
            user_roles=["developer"],
            team_id="engineering"
        )
        
        assert "team-engineering-db-password" in secrets
        assert secrets["team-engineering-db-password"] == "team-secret-456"
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_get_secrets_for_user_with_role_secrets(self, mock_boto_client):
        """Test getting role-based secrets."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        # Mock list_secrets to return role-based secret
        mock_secrets.list_secrets.return_value = {
            "SecretList": [{"Name": "role-admin-master-key"}]
        }
        
        mock_secrets.get_secret_value.return_value = {
            "SecretString": "role-secret-789"
        }
        
        service = SecretsService(region="us-west-2")
        secrets = service.get_secrets_for_user(
            user_id="jdoe",
            user_roles=["admin"]
        )
        
        assert "role-admin-master-key" in secrets
        assert secrets["role-admin-master-key"] == "role-secret-789"
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_inject_secrets_at_launch(self, mock_boto_client):
        """Test injecting secrets at WorkSpace launch."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        mock_secrets.list_secrets.return_value = {
            "SecretList": [{"Name": "user-jdoe-api-key"}]
        }
        
        mock_secrets.get_secret_value.return_value = {
            "SecretString": "secret-value-123"
        }
        
        service = SecretsService(region="us-west-2")
        result = service.inject_secrets_at_launch(
            workspace_id="ws-123",
            user_id="jdoe",
            user_roles=["developer"]
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["user_id"] == "jdoe"
        assert result["injected_count"] == 1
        assert "user-jdoe-api-key" in result["secret_names"]
        assert "injected_at" in result
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_inject_secrets_at_launch_no_secrets(self, mock_boto_client):
        """Test injecting secrets when no secrets found."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        mock_secrets.list_secrets.return_value = {
            "SecretList": []
        }
        
        service = SecretsService(region="us-west-2")
        result = service.inject_secrets_at_launch(
            workspace_id="ws-123",
            user_id="jdoe",
            user_roles=["developer"]
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["injected_count"] == 0
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_handle_secret_rotation_success(self, mock_boto_client):
        """Test successful secret rotation."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        mock_secrets.get_secret_value.return_value = {
            "SecretString": "new-secret-value"
        }
        
        service = SecretsService(region="us-west-2")
        result = service.handle_secret_rotation(
            secret_name="api-key",
            affected_workspaces=["ws-123", "ws-456"]
        )
        
        assert result["secret_name"] == "api-key"
        assert len(result["updated_workspaces"]) == 2
        assert len(result["failed_workspaces"]) == 0
        assert result["within_timeout"] is True
        assert result["duration_minutes"] <= 5
        assert "rotated_at" in result
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_handle_secret_rotation_partial_failure(self, mock_boto_client):
        """Test secret rotation with partial failures."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        mock_secrets.get_secret_value.return_value = {
            "SecretString": "new-secret-value"
        }
        
        service = SecretsService(region="us-west-2")
        
        # Mock _update_environment_variable to fail for second workspace
        call_count = 0
        def mock_update(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count == 1
        
        service._update_environment_variable = mock_update
        
        result = service.handle_secret_rotation(
            secret_name="api-key",
            affected_workspaces=["ws-123", "ws-456"]
        )
        
        assert len(result["updated_workspaces"]) == 1
        assert len(result["failed_workspaces"]) == 1
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_configure_secret_rotation(self, mock_boto_client):
        """Test configuring secret rotation."""
        from src.provisioning.secrets_service import SecretsService
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        service = SecretsService(region="us-west-2")
        result = service.configure_secret_rotation(
            secret_name="api-key",
            rotation_days=30
        )
        
        assert result is True
        mock_secrets.rotate_secret.assert_called_once_with(
            SecretId="api-key",
            RotationRules={"AutomaticallyAfterDays": 30}
        )
    
    @patch('src.provisioning.secrets_service.boto3.client')
    def test_get_secret_metadata(self, mock_boto_client):
        """Test getting secret metadata."""
        from src.provisioning.secrets_service import SecretsService
        from datetime import datetime
        
        mock_secrets = Mock()
        mock_ssm = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: mock_secrets if service == "secretsmanager" else mock_ssm
        
        mock_secrets.describe_secret.return_value = {
            "Name": "api-key",
            "ARN": "arn:aws:secretsmanager:us-west-2:123456789012:secret:api-key",
            "Description": "API key for external service",
            "RotationEnabled": True,
            "RotationRules": {"AutomaticallyAfterDays": 30},
            "LastRotatedDate": datetime.utcnow(),
            "LastChangedDate": datetime.utcnow(),
            "Tags": [{"Key": "Environment", "Value": "production"}]
        }
        
        service = SecretsService(region="us-west-2")
        metadata = service.get_secret_metadata("api-key")
        
        assert metadata is not None
        assert metadata["name"] == "api-key"
        assert metadata["rotation_enabled"] is True
        assert metadata["rotation_rules"]["AutomaticallyAfterDays"] == 30
        assert "last_rotated" in metadata
        assert len(metadata["tags"]) == 1



class TestPoolManager:
    """Test pre-warmed WorkSpace pool manager."""
    
    def test_initialize_pool(self):
        """Test pool initialization."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(
            workspaces_client=mock_client,
            min_pool_size=5,
            max_pool_size=20
        )
        
        result = manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        assert result["blueprint_id"] == "robotics-v3"
        assert result["operating_system"] == "LINUX"
        assert result["min_size"] == 5
        assert result["max_size"] == 20
        assert result["current_size"] == 5
        assert "initialized_at" in result
    
    def test_get_available_workspace_success(self):
        """Test getting available WorkSpace from pool."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(workspaces_client=mock_client)
        
        # Initialize pool
        manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        # Get WorkSpace from pool
        workspace = manager.get_available_workspace(
            blueprint_id="robotics-v3",
            operating_system="LINUX"
        )
        
        assert workspace is not None
        assert workspace["blueprint_id"] == "robotics-v3"
        assert workspace["status"] == "assigned"
        assert "assigned_at" in workspace
    
    def test_get_available_workspace_pool_empty(self):
        """Test getting WorkSpace when pool is empty."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(workspaces_client=mock_client)
        
        # Try to get from non-existent pool
        workspace = manager.get_available_workspace(
            blueprint_id="nonexistent",
            operating_system="LINUX"
        )
        
        assert workspace is None
    
    def test_replenish_pool_below_minimum(self):
        """Test pool replenishment when below minimum."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(
            workspaces_client=mock_client,
            min_pool_size=5
        )
        
        # Initialize pool
        manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        # Assign 3 WorkSpaces
        for _ in range(3):
            manager.get_available_workspace(
                blueprint_id="robotics-v3",
                operating_system="LINUX"
            )
        
        # Replenish pool
        result = manager.replenish_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        assert result["replenished"] is True
        assert result["provisioned_count"] == 3
        assert result["available_count"] == 5
    
    def test_replenish_pool_above_minimum(self):
        """Test pool replenishment when above minimum."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(
            workspaces_client=mock_client,
            min_pool_size=5
        )
        
        # Initialize pool
        manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        # Pool already at minimum, no replenishment needed
        result = manager.replenish_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        assert result["replenished"] is False
        assert result["reason"] == "above_minimum"
        assert result["available_count"] == 5
    
    def test_get_pool_status(self):
        """Test getting pool status."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(workspaces_client=mock_client)
        
        # Initialize pool
        manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        # Get status
        status = manager.get_pool_status(
            blueprint_id="robotics-v3",
            operating_system="LINUX"
        )
        
        assert status["exists"] is True
        assert status["blueprint_id"] == "robotics-v3"
        assert status["total_size"] == 5
        assert status["status_counts"]["available"] == 5
        assert "checked_at" in status
    
    def test_adjust_pool_size_based_on_demand(self):
        """Test pool size adjustment based on demand."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(
            workspaces_client=mock_client,
            min_pool_size=5,
            max_pool_size=20
        )
        
        # Adjust based on demand pattern
        demand_pattern = {
            "avg_requests_per_hour": 8,
            "peak_requests_per_hour": 15
        }
        
        result = manager.adjust_pool_size(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            demand_pattern=demand_pattern
        )
        
        assert result["target_size"] == 18  # 15 * 1.2 = 18
        assert result["avg_requests_per_hour"] == 8
        assert result["peak_requests_per_hour"] == 15
        assert "adjusted_at" in result
    
    def test_adjust_pool_size_capped_at_max(self):
        """Test pool size adjustment capped at maximum."""
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        manager = PoolManager(
            workspaces_client=mock_client,
            min_pool_size=5,
            max_pool_size=20
        )
        
        # High demand that would exceed max
        demand_pattern = {
            "avg_requests_per_hour": 50,
            "peak_requests_per_hour": 100
        }
        
        result = manager.adjust_pool_size(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            demand_pattern=demand_pattern
        )
        
        assert result["target_size"] == 20  # Capped at max_pool_size


class TestPoolAssignmentService:
    """Test pool assignment service."""
    
    def test_assign_workspace_success(self):
        """Test successful WorkSpace assignment from pool."""
        from src.provisioning.pool_assignment import PoolAssignmentService
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        mock_volume_service = Mock()
        mock_secrets_service = Mock()
        
        # Setup pool manager
        pool_manager = PoolManager(workspaces_client=mock_client)
        pool_manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        # Setup mocks
        mock_volume_service.attach_volume_to_workspace.return_value = True
        mock_volume_service.sync_dotfiles_to_workspace.return_value = {
            "within_timeout": True,
            "synced_files": [".bashrc", ".vimrc"]
        }
        mock_secrets_service.inject_secrets_at_launch.return_value = {
            "injected_count": 2
        }
        
        # Create assignment service
        assignment_service = PoolAssignmentService(
            pool_manager=pool_manager,
            user_volume_service=mock_volume_service,
            secrets_service=mock_secrets_service
        )
        
        # Assign WorkSpace
        result = assignment_service.assign_workspace(
            user_id="jdoe",
            user_roles=["developer"],
            blueprint_id="robotics-v3",
            operating_system="LINUX"
        )
        
        assert result["assigned"] is True
        assert result["user_id"] == "jdoe"
        assert result["blueprint_id"] == "robotics-v3"
        assert "workspace_id" in result
        assert result["customization"]["success"] is True
    
    def test_assign_workspace_pool_empty(self):
        """Test WorkSpace assignment when pool is empty."""
        from src.provisioning.pool_assignment import PoolAssignmentService
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        mock_volume_service = Mock()
        mock_secrets_service = Mock()
        
        # Setup empty pool manager
        pool_manager = PoolManager(workspaces_client=mock_client)
        
        # Create assignment service
        assignment_service = PoolAssignmentService(
            pool_manager=pool_manager,
            user_volume_service=mock_volume_service,
            secrets_service=mock_secrets_service
        )
        
        # Try to assign from empty pool
        result = assignment_service.assign_workspace(
            user_id="jdoe",
            user_roles=["developer"],
            blueprint_id="nonexistent",
            operating_system="LINUX"
        )
        
        assert result["assigned"] is False
        assert result["reason"] == "pool_empty"
        assert result["fallback_required"] is True
    
    def test_assign_workspace_customization_failure(self):
        """Test WorkSpace assignment with customization failure."""
        from src.provisioning.pool_assignment import PoolAssignmentService
        from src.provisioning.pool_manager import PoolManager
        
        mock_client = Mock()
        mock_volume_service = Mock()
        mock_secrets_service = Mock()
        
        # Setup pool manager
        pool_manager = PoolManager(workspaces_client=mock_client)
        pool_manager.initialize_pool(
            blueprint_id="robotics-v3",
            operating_system="LINUX",
            bundle_id="wsb-performance",
            directory_id="d-123"
        )
        
        # Setup mocks to fail
        mock_volume_service.attach_volume_to_workspace.return_value = False
        mock_secrets_service.inject_secrets_at_launch.return_value = {
            "injected_count": 0
        }
        
        # Create assignment service
        assignment_service = PoolAssignmentService(
            pool_manager=pool_manager,
            user_volume_service=mock_volume_service,
            secrets_service=mock_secrets_service
        )
        
        # Assign WorkSpace
        result = assignment_service.assign_workspace(
            user_id="jdoe",
            user_roles=["developer"],
            blueprint_id="robotics-v3",
            operating_system="LINUX"
        )
        
        assert result["assigned"] is False
        assert result["reason"] == "customization_failed"



class TestLifecycleManager:
    """Test WorkSpace lifecycle management."""
    
    def test_check_idle_timeout_exceeded(self):
        """Test idle timeout check when exceeded."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(
            workspaces_client=mock_client,
            default_idle_timeout_minutes=60
        )
        
        # WorkSpace idle for 90 minutes
        last_activity = datetime.utcnow() - timedelta(minutes=90)
        
        result = manager.check_idle_timeout(
            workspace_id="ws-123",
            last_activity_time=last_activity
        )
        
        assert result["exceeded"] is True
        assert result["idle_minutes"] >= 90
        assert result["timeout_minutes"] == 60
    
    def test_check_idle_timeout_not_exceeded(self):
        """Test idle timeout check when not exceeded."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace idle for 30 minutes
        last_activity = datetime.utcnow() - timedelta(minutes=30)
        
        result = manager.check_idle_timeout(
            workspace_id="ws-123",
            last_activity_time=last_activity,
            idle_timeout_minutes=60
        )
        
        assert result["exceeded"] is False
        assert result["idle_minutes"] < 60
    
    def test_auto_stop_idle_workspace(self):
        """Test auto-stopping idle WorkSpace."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace idle for 90 minutes
        last_activity = datetime.utcnow() - timedelta(minutes=90)
        
        result = manager.auto_stop_idle_workspace(
            workspace_id="ws-123",
            last_activity_time=last_activity,
            idle_timeout_minutes=60
        )
        
        assert result["stopped"] is True
        assert result["reason"] == "idle_timeout"
        assert "stopped_at" in result
    
    def test_auto_stop_not_idle_workspace(self):
        """Test not stopping WorkSpace that's not idle."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace idle for 30 minutes
        last_activity = datetime.utcnow() - timedelta(minutes=30)
        
        result = manager.auto_stop_idle_workspace(
            workspace_id="ws-123",
            last_activity_time=last_activity,
            idle_timeout_minutes=60
        )
        
        assert result["stopped"] is False
        assert result["reason"] == "not_idle"
    
    def test_check_maximum_lifetime_exceeded(self):
        """Test maximum lifetime check when exceeded."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(
            workspaces_client=mock_client,
            default_max_lifetime_days=90
        )
        
        # WorkSpace created 100 days ago
        created_time = datetime.utcnow() - timedelta(days=100)
        
        result = manager.check_maximum_lifetime(
            workspace_id="ws-123",
            created_time=created_time
        )
        
        assert result["exceeded"] is True
        assert result["age_days"] >= 100
        assert result["lifetime_days"] == 90
    
    def test_check_maximum_lifetime_not_exceeded(self):
        """Test maximum lifetime check when not exceeded."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace created 30 days ago
        created_time = datetime.utcnow() - timedelta(days=30)
        
        result = manager.check_maximum_lifetime(
            workspace_id="ws-123",
            created_time=created_time,
            max_lifetime_days=90
        )
        
        assert result["exceeded"] is False
        assert result["age_days"] < 90
    
    def test_auto_terminate_expired_workspace(self):
        """Test auto-terminating expired WorkSpace."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace created 100 days ago
        created_time = datetime.utcnow() - timedelta(days=100)
        
        result = manager.auto_terminate_expired_workspace(
            workspace_id="ws-123",
            created_time=created_time,
            max_lifetime_days=90
        )
        
        assert result["terminated"] is True
        assert result["reason"] == "max_lifetime"
        assert "terminated_at" in result
    
    def test_auto_terminate_not_expired_workspace(self):
        """Test not terminating WorkSpace that's not expired."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace created 30 days ago
        created_time = datetime.utcnow() - timedelta(days=30)
        
        result = manager.auto_terminate_expired_workspace(
            workspace_id="ws-123",
            created_time=created_time,
            max_lifetime_days=90
        )
        
        assert result["terminated"] is False
        assert result["reason"] == "not_expired"
    
    def test_check_stale_workspace_is_stale(self):
        """Test checking stale WorkSpace."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace stopped 35 days ago
        stopped_time = datetime.utcnow() - timedelta(days=35)
        
        result = manager.check_stale_workspace(
            workspace_id="ws-123",
            stopped_time=stopped_time
        )
        
        assert result["is_stale"] is True
        assert result["stopped_days"] >= 30
    
    def test_check_stale_workspace_not_stale(self):
        """Test checking WorkSpace that's not stale."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace stopped 15 days ago
        stopped_time = datetime.utcnow() - timedelta(days=15)
        
        result = manager.check_stale_workspace(
            workspace_id="ws-123",
            stopped_time=stopped_time
        )
        
        assert result["is_stale"] is False
        assert result["stopped_days"] < 30
    
    def test_check_stale_workspace_with_keep_alive(self):
        """Test checking stale WorkSpace with keep-alive flag."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace stopped 35 days ago but has keep-alive
        stopped_time = datetime.utcnow() - timedelta(days=35)
        
        result = manager.check_stale_workspace(
            workspace_id="ws-123",
            stopped_time=stopped_time,
            keep_alive=True
        )
        
        assert result["is_stale"] is False
        assert result["reason"] == "keep_alive_enabled"
    
    def test_flag_stale_workspace(self):
        """Test flagging stale WorkSpace."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace stopped 35 days ago
        stopped_time = datetime.utcnow() - timedelta(days=35)
        
        result = manager.flag_stale_workspace(
            workspace_id="ws-123",
            owner_id="jdoe",
            stopped_time=stopped_time
        )
        
        assert result["flagged"] is True
        assert result["owner_id"] == "jdoe"
        assert result["notification_sent"] is True
        assert "flagged_at" in result
    
    def test_flag_stale_workspace_not_stale(self):
        """Test not flagging WorkSpace that's not stale."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace stopped 15 days ago
        stopped_time = datetime.utcnow() - timedelta(days=15)
        
        result = manager.flag_stale_workspace(
            workspace_id="ws-123",
            owner_id="jdoe",
            stopped_time=stopped_time
        )
        
        assert result["flagged"] is False
        assert result["reason"] == "not_stale"
    
    def test_terminate_stale_workspace_after_grace_period(self):
        """Test terminating stale WorkSpace after grace period."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace flagged 10 days ago
        flagged_time = datetime.utcnow() - timedelta(days=10)
        
        result = manager.terminate_stale_workspace(
            workspace_id="ws-123",
            flagged_time=flagged_time
        )
        
        assert result["terminated"] is True
        assert result["reason"] == "stale_grace_period_expired"
        assert "terminated_at" in result
    
    def test_terminate_stale_workspace_in_grace_period(self):
        """Test not terminating stale WorkSpace still in grace period."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace flagged 3 days ago
        flagged_time = datetime.utcnow() - timedelta(days=3)
        
        result = manager.terminate_stale_workspace(
            workspace_id="ws-123",
            flagged_time=flagged_time
        )
        
        assert result["terminated"] is False
        assert result["reason"] == "grace_period_not_expired"
    
    def test_terminate_stale_workspace_with_keep_alive(self):
        """Test not terminating stale WorkSpace with keep-alive flag."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # WorkSpace flagged 10 days ago but has keep-alive
        flagged_time = datetime.utcnow() - timedelta(days=10)
        
        result = manager.terminate_stale_workspace(
            workspace_id="ws-123",
            flagged_time=flagged_time,
            keep_alive=True
        )
        
        assert result["terminated"] is False
        assert result["reason"] == "keep_alive_enabled"
    
    def test_scan_and_cleanup_workspaces(self):
        """Test scanning and cleaning up WorkSpaces."""
        from src.provisioning.lifecycle_manager import LifecycleManager
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        manager = LifecycleManager(workspaces_client=mock_client)
        
        # Create test WorkSpaces
        workspaces = [
            {
                "workspace_id": "ws-idle",
                "state": "AVAILABLE",
                "last_activity_time": datetime.utcnow() - timedelta(minutes=90),
                "created_time": datetime.utcnow() - timedelta(days=10),
                "idle_timeout_minutes": 60
            },
            {
                "workspace_id": "ws-expired",
                "state": "AVAILABLE",
                "last_activity_time": datetime.utcnow() - timedelta(minutes=10),
                "created_time": datetime.utcnow() - timedelta(days=100),
                "max_lifetime_days": 90
            },
            {
                "workspace_id": "ws-stale",
                "state": "STOPPED",
                "stopped_time": datetime.utcnow() - timedelta(days=35),
                "created_time": datetime.utcnow() - timedelta(days=50),
                "owner_id": "jdoe",
                "is_stale": False
            }
        ]
        
        result = manager.scan_and_cleanup_workspaces(workspaces)
        
        assert result["scanned_count"] == 3
        assert result["stopped_count"] == 1  # ws-idle
        assert result["terminated_count"] == 1  # ws-expired
        assert result["flagged_count"] == 1  # ws-stale



class TestProvisioningMonitor:
    """Test provisioning time monitoring."""
    
    def test_start_provisioning(self):
        """Test starting provisioning tracking."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        result = monitor.start_provisioning(
            workspace_id="ws-123",
            user_id="jdoe",
            blueprint_id="robotics-v3",
            bundle_type="PERFORMANCE"
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["status"] == "requested"
        assert "start_time" in result
    
    def test_complete_provisioning_within_sla(self):
        """Test completing provisioning within SLA."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        # Start tracking
        monitor.start_provisioning(
            workspace_id="ws-123",
            user_id="jdoe",
            blueprint_id="robotics-v3",
            bundle_type="PERFORMANCE"
        )
        
        # Complete immediately (within SLA)
        result = monitor.complete_provisioning(
            workspace_id="ws-123",
            success=True
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["success"] is True
        assert result["exceeded_sla"] is False
        assert result["duration_seconds"] < 300
    
    def test_complete_provisioning_exceeds_sla(self):
        """Test completing provisioning that exceeds SLA."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        from datetime import datetime, timedelta
        
        monitor = ProvisioningMonitor()
        
        # Start tracking
        monitor.start_provisioning(
            workspace_id="ws-123",
            user_id="jdoe",
            blueprint_id="robotics-v3",
            bundle_type="PERFORMANCE"
        )
        
        # Manually set start time to 6 minutes ago
        monitor.provisioning_requests["ws-123"]["start_time"] = datetime.utcnow() - timedelta(minutes=6)
        
        # Complete provisioning
        result = monitor.complete_provisioning(
            workspace_id="ws-123",
            success=True
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["exceeded_sla"] is True
        assert result["duration_seconds"] > 300
    
    def test_complete_provisioning_failed(self):
        """Test completing failed provisioning."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        # Start tracking
        monitor.start_provisioning(
            workspace_id="ws-123",
            user_id="jdoe",
            blueprint_id="robotics-v3",
            bundle_type="PERFORMANCE"
        )
        
        # Complete with failure
        result = monitor.complete_provisioning(
            workspace_id="ws-123",
            success=False
        )
        
        assert result["workspace_id"] == "ws-123"
        assert result["success"] is False
    
    def test_get_provisioning_status_in_progress(self):
        """Test getting status of in-progress provisioning."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        # Start tracking
        monitor.start_provisioning(
            workspace_id="ws-123",
            user_id="jdoe",
            blueprint_id="robotics-v3",
            bundle_type="PERFORMANCE"
        )
        
        # Get status
        status = monitor.get_provisioning_status("ws-123")
        
        assert status is not None
        assert status["workspace_id"] == "ws-123"
        assert status["status"] == "requested"
        assert status["currently_exceeding_sla"] is False
        assert "current_duration_seconds" in status
    
    def test_get_provisioning_status_not_found(self):
        """Test getting status for non-existent provisioning."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        status = monitor.get_provisioning_status("ws-nonexistent")
        
        assert status is None
    
    def test_get_provisioning_metrics_empty(self):
        """Test getting metrics with no data."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        metrics = monitor.get_provisioning_metrics(time_period_hours=24)
        
        assert metrics["total_requests"] == 0
        assert metrics["success_rate"] == 0.0
        assert metrics["sla_compliance_rate"] == 0.0
    
    def test_get_provisioning_metrics_with_data(self):
        """Test getting metrics with provisioning data."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        # Create multiple provisioning requests
        for i in range(5):
            workspace_id = f"ws-{i}"
            monitor.start_provisioning(
                workspace_id=workspace_id,
                user_id="jdoe",
                blueprint_id="robotics-v3",
                bundle_type="PERFORMANCE"
            )
            monitor.complete_provisioning(
                workspace_id=workspace_id,
                success=True
            )
        
        # Get metrics
        metrics = monitor.get_provisioning_metrics(time_period_hours=24)
        
        assert metrics["total_requests"] == 5
        assert metrics["successful_requests"] == 5
        assert metrics["failed_requests"] == 0
        assert metrics["success_rate"] == 100.0
        assert metrics["avg_duration_seconds"] >= 0
        assert metrics["sla_compliance_rate"] == 100.0
    
    def test_get_provisioning_metrics_with_failures(self):
        """Test getting metrics with some failures."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        
        monitor = ProvisioningMonitor()
        
        # Create provisioning requests with some failures
        for i in range(10):
            workspace_id = f"ws-{i}"
            monitor.start_provisioning(
                workspace_id=workspace_id,
                user_id="jdoe",
                blueprint_id="robotics-v3",
                bundle_type="PERFORMANCE"
            )
            # Fail 2 out of 10
            success = i not in [3, 7]
            monitor.complete_provisioning(
                workspace_id=workspace_id,
                success=success
            )
        
        # Get metrics
        metrics = monitor.get_provisioning_metrics(time_period_hours=24)
        
        assert metrics["total_requests"] == 10
        assert metrics["successful_requests"] == 8
        assert metrics["failed_requests"] == 2
        assert metrics["success_rate"] == 80.0
    
    def test_get_provisioning_metrics_with_sla_violations(self):
        """Test getting metrics with SLA violations."""
        from src.provisioning.provisioning_monitor import ProvisioningMonitor
        from datetime import datetime, timedelta
        
        monitor = ProvisioningMonitor()
        
        # Create provisioning requests with some SLA violations
        for i in range(5):
            workspace_id = f"ws-{i}"
            monitor.start_provisioning(
                workspace_id=workspace_id,
                user_id="jdoe",
                blueprint_id="robotics-v3",
                bundle_type="PERFORMANCE"
            )
            
            # Make 2 requests exceed SLA
            if i in [1, 3]:
                monitor.provisioning_requests[workspace_id]["start_time"] = datetime.utcnow() - timedelta(minutes=6)
            
            monitor.complete_provisioning(
                workspace_id=workspace_id,
                success=True
            )
        
        # Get metrics
        metrics = monitor.get_provisioning_metrics(time_period_hours=24)
        
        assert metrics["total_requests"] == 5
        assert metrics["sla_violations"] == 2
        assert metrics["sla_compliance_rate"] == 60.0

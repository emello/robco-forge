"""Okta SSO integration using SAML 2.0."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from .jwt_manager import JWTManager

logger = logging.getLogger(__name__)


class OktaSSOHandler:
    """Handles Okta SSO authentication using SAML 2.0 protocol.
    
    Requirements:
    - 8.1: SSO authentication via Okta using SAML 2.0
    - 8.2: Multi-factor authentication requirement
    """
    
    def __init__(
        self,
        okta_metadata_url: str,
        sp_entity_id: str,
        sp_acs_url: str,
        sp_sls_url: str,
        jwt_manager: JWTManager,
    ):
        """Initialize Okta SSO handler.
        
        Args:
            okta_metadata_url: URL to Okta SAML metadata
            sp_entity_id: Service Provider entity ID
            sp_acs_url: Assertion Consumer Service URL (callback)
            sp_sls_url: Single Logout Service URL
            jwt_manager: JWT token manager instance
        """
        self.okta_metadata_url = okta_metadata_url
        self.sp_entity_id = sp_entity_id
        self.sp_acs_url = sp_acs_url
        self.sp_sls_url = sp_sls_url
        self.jwt_manager = jwt_manager
        
        # SAML settings will be loaded dynamically per request
        self._saml_settings: Optional[Dict[str, Any]] = None
    
    def _get_saml_settings(self) -> Dict[str, Any]:
        """Get SAML settings configuration.
        
        Returns:
            SAML settings dictionary
        """
        if self._saml_settings is None:
            self._saml_settings = {
                "strict": True,
                "debug": False,
                "sp": {
                    "entityId": self.sp_entity_id,
                    "assertionConsumerService": {
                        "url": self.sp_acs_url,
                        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                    },
                    "singleLogoutService": {
                        "url": self.sp_sls_url,
                        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                    },
                    "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                    "x509cert": "",
                    "privateKey": ""
                },
                "idp": {
                    "entityId": "",  # Will be loaded from metadata
                    "singleSignOnService": {
                        "url": "",  # Will be loaded from metadata
                        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                    },
                    "singleLogoutService": {
                        "url": "",  # Will be loaded from metadata
                        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                    },
                    "x509cert": ""  # Will be loaded from metadata
                },
                "security": {
                    "nameIdEncrypted": False,
                    "authnRequestsSigned": True,
                    "logoutRequestSigned": True,
                    "logoutResponseSigned": True,
                    "signMetadata": True,
                    "wantMessagesSigned": True,
                    "wantAssertionsSigned": True,
                    "wantNameId": True,
                    "wantNameIdEncrypted": False,
                    "wantAssertionsEncrypted": False,
                    "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                    "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
                    "requestedAuthnContext": ["urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"],
                    "requestedAuthnContextComparison": "exact",
                }
            }
        return self._saml_settings
    
    def prepare_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for SAML auth.
        
        Args:
            request_data: HTTP request data (method, url, query_string, post_data)
            
        Returns:
            Prepared request dictionary for OneLogin SAML library
        """
        return {
            "https": "on" if request_data.get("https", True) else "off",
            "http_host": request_data.get("http_host", ""),
            "script_name": request_data.get("script_name", ""),
            "server_port": request_data.get("server_port", 443),
            "get_data": request_data.get("get_data", {}),
            "post_data": request_data.get("post_data", {}),
        }
    
    def initiate_login(self, request_data: Dict[str, Any], relay_state: Optional[str] = None) -> str:
        """Initiate SSO login by generating SAML AuthnRequest.
        
        Args:
            request_data: HTTP request data
            relay_state: Optional relay state to preserve after authentication
            
        Returns:
            Redirect URL to Okta SSO login page
            
        Validates: Requirements 8.1
        """
        try:
            prepared_request = self.prepare_request(request_data)
            auth = OneLogin_Saml2_Auth(prepared_request, self._get_saml_settings())
            
            # Generate SAML AuthnRequest and get redirect URL
            sso_url = auth.login(return_to=relay_state)
            
            logger.info("SSO login initiated", extra={"relay_state": relay_state})
            return sso_url
            
        except Exception as e:
            logger.error(f"Failed to initiate SSO login: {e}", exc_info=True)
            raise SSOAuthenticationError(f"Failed to initiate SSO login: {e}")
    
    def handle_callback(
        self,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle SAML callback from Okta after authentication.
        
        Args:
            request_data: HTTP request data containing SAML response
            
        Returns:
            Dictionary containing:
                - user_id: User identifier
                - email: User email
                - name: User full name
                - roles: List of user roles
                - mfa_verified: Whether MFA was completed
                - jwt_token: Generated JWT token
                - relay_state: Original relay state if provided
                
        Raises:
            SSOAuthenticationError: If SAML response is invalid or MFA not verified
            
        Validates: Requirements 8.1, 8.2
        """
        try:
            prepared_request = self.prepare_request(request_data)
            auth = OneLogin_Saml2_Auth(prepared_request, self._get_saml_settings())
            
            # Process SAML response
            auth.process_response()
            errors = auth.get_errors()
            
            if errors:
                error_reason = auth.get_last_error_reason()
                logger.error(
                    f"SAML authentication failed: {error_reason}",
                    extra={"errors": errors}
                )
                raise SSOAuthenticationError(f"SAML authentication failed: {error_reason}")
            
            # Check if user is authenticated
            if not auth.is_authenticated():
                logger.warning("User not authenticated after SAML response")
                raise SSOAuthenticationError("User not authenticated")
            
            # Extract user attributes from SAML assertion
            attributes = auth.get_attributes()
            name_id = auth.get_nameid()
            
            # Verify MFA was completed (check for MFA assertion in SAML response)
            # Okta includes AuthnContextClassRef indicating MFA completion
            authn_context = auth.get_last_authn_context()
            mfa_verified = self._verify_mfa_context(authn_context)
            
            if not mfa_verified:
                logger.warning(
                    f"MFA not verified for user {name_id}",
                    extra={"authn_context": authn_context}
                )
                raise MFARequiredError("Multi-factor authentication is required")
            
            # Extract user information
            user_data = {
                "user_id": name_id,
                "email": attributes.get("email", [name_id])[0] if attributes.get("email") else name_id,
                "name": attributes.get("name", [""])[0] if attributes.get("name") else "",
                "roles": attributes.get("roles", []),
                "mfa_verified": mfa_verified,
            }
            
            # Generate JWT token
            jwt_token = self.jwt_manager.generate_token(
                user_id=user_data["user_id"],
                email=user_data["email"],
                roles=user_data["roles"],
            )
            
            user_data["jwt_token"] = jwt_token
            user_data["relay_state"] = auth.get_last_request_id()
            
            logger.info(
                f"SSO authentication successful for user {user_data['user_id']}",
                extra={"email": user_data["email"], "mfa_verified": mfa_verified}
            )
            
            return user_data
            
        except (SSOAuthenticationError, MFARequiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to handle SSO callback: {e}", exc_info=True)
            raise SSOAuthenticationError(f"Failed to handle SSO callback: {e}")
    
    def _verify_mfa_context(self, authn_context: Optional[str]) -> bool:
        """Verify that MFA was completed based on SAML AuthnContext.
        
        Args:
            authn_context: SAML AuthnContextClassRef value
            
        Returns:
            True if MFA was verified, False otherwise
            
        Validates: Requirements 8.2
        """
        # Okta MFA contexts that indicate MFA completion
        mfa_contexts = [
            "urn:oasis:names:tc:SAML:2.0:ac:classes:MultiFactor",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:MultiFactorContract",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:TimeSyncToken",
            "http://schemas.microsoft.com/claims/multipleauthn",
        ]
        
        if not authn_context:
            return False
        
        return any(mfa_ctx in authn_context for mfa_ctx in mfa_contexts)
    
    def logout(self, request_data: Dict[str, Any], name_id: str, session_index: Optional[str] = None) -> str:
        """Initiate SSO logout.
        
        Args:
            request_data: HTTP request data
            name_id: User's SAML NameID
            session_index: Optional SAML session index
            
        Returns:
            Redirect URL to Okta logout page
        """
        try:
            prepared_request = self.prepare_request(request_data)
            auth = OneLogin_Saml2_Auth(prepared_request, self._get_saml_settings())
            
            # Generate SAML LogoutRequest
            logout_url = auth.logout(
                name_id=name_id,
                session_index=session_index,
            )
            
            logger.info(f"SSO logout initiated for user {name_id}")
            return logout_url
            
        except Exception as e:
            logger.error(f"Failed to initiate SSO logout: {e}", exc_info=True)
            raise SSOAuthenticationError(f"Failed to initiate SSO logout: {e}")


class SSOAuthenticationError(Exception):
    """Raised when SSO authentication fails."""
    pass


class MFARequiredError(Exception):
    """Raised when MFA is required but not completed."""
    pass

"""JWT token generation and validation."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

logger = logging.getLogger(__name__)


class JWTManager:
    """Manages JWT token generation and validation.
    
    Requirements:
    - 8.1: Generate JWT tokens after SSO authentication
    - 8.5: Support time-bound credentials for contractors
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
    ):
        """Initialize JWT manager.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def generate_token(
        self,
        user_id: str,
        email: str,
        roles: List[str],
        token_type: str = "access",
        custom_expiry: Optional[datetime] = None,
    ) -> str:
        """Generate JWT token for authenticated user.
        
        Args:
            user_id: User identifier
            email: User email
            roles: List of user roles
            token_type: Token type ("access" or "refresh")
            custom_expiry: Custom expiration datetime (for contractor time-bound credentials)
            
        Returns:
            Encoded JWT token string
            
        Validates: Requirements 8.1, 8.5
        """
        now = datetime.utcnow()
        
        # Determine expiration time
        if custom_expiry:
            # Custom expiry for time-bound credentials (contractors)
            expire = custom_expiry
        elif token_type == "access":
            expire = now + timedelta(minutes=self.access_token_expire_minutes)
        else:  # refresh token
            expire = now + timedelta(days=self.refresh_token_expire_days)
        
        # Build JWT payload
        payload = {
            "sub": user_id,  # Subject (user ID)
            "email": email,
            "roles": roles,
            "type": token_type,
            "iat": now,  # Issued at
            "exp": expire,  # Expiration
            "nbf": now,  # Not before
        }
        
        # Encode token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(
            f"Generated {token_type} token for user {user_id}",
            extra={
                "user_id": user_id,
                "email": email,
                "roles": roles,
                "expires_at": expire.isoformat(),
            }
        )
        
        return token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and extract payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload containing user_id, email, roles, etc.
            
        Raises:
            InvalidTokenError: If token is invalid
            ExpiredSignatureError: If token has expired
            
        Validates: Requirements 8.1
        """
        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                }
            )
            
            logger.debug(
                f"Token validated for user {payload.get('sub')}",
                extra={"user_id": payload.get("sub")}
            )
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token validation failed: token expired")
            raise TokenExpiredError("Token has expired")
        except InvalidTokenError as e:
            logger.warning(f"Token validation failed: {e}")
            raise TokenInvalidError(f"Invalid token: {e}")
    
    def refresh_token(self, refresh_token: str) -> str:
        """Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            TokenInvalidError: If refresh token is invalid or not a refresh token
        """
        try:
            payload = self.validate_token(refresh_token)
            
            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise TokenInvalidError("Token is not a refresh token")
            
            # Generate new access token
            return self.generate_token(
                user_id=payload["sub"],
                email=payload["email"],
                roles=payload["roles"],
                token_type="access",
            )
            
        except (TokenExpiredError, TokenInvalidError):
            raise
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}", exc_info=True)
            raise TokenInvalidError(f"Failed to refresh token: {e}")
    
    def extract_user_from_token(self, token: str) -> Dict[str, Any]:
        """Extract user information from token without full validation.
        
        Useful for logging/debugging purposes. Does not verify signature or expiration.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary with user_id, email, roles
        """
        try:
            # Decode without verification (for inspection only)
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=[self.algorithm]
            )
            
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
            }
        except Exception as e:
            logger.warning(f"Failed to extract user from token: {e}")
            return {}


class TokenExpiredError(Exception):
    """Raised when JWT token has expired."""
    pass


class TokenInvalidError(Exception):
    """Raised when JWT token is invalid."""
    pass

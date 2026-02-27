"""
ResilAI Configuration Module

Uses pydantic-settings for type-safe configuration with validation.
Loads .env file only in local environment mode.
"""

import os
import sys
from enum import Enum
from typing import Optional, List, Dict
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Deployment Validation
# =============================================================================

class DeploymentValidationError(Exception):
    """
    Raised when deployment configuration is invalid.
    
    This error causes application startup to fail immediately,
    preventing accidental cross-environment deployments.
    """
    pass


# Expected Firebase/GCP project IDs for each environment.
# CRITICAL: These mappings enforce branch → environment isolation.
# If ENV=demo but PROJECT_ID points to staging, the app will crash.
EXPECTED_PROJECT_IDS: Dict[str, str] = {
    "demo": "gen-lang-client-0384513977",
    "staging": "gen-lang-client-0384513977",  # Same project, different env
    "local": "",  # Local can use any project or none
}


def validate_deployment() -> None:
    """
    Validate that the deployment environment matches expected project.
    
    Must be called at application startup. Crashes immediately on mismatch
    to prevent accidental dual-environment deployments.
    
    Raises:
        DeploymentValidationError: If ENV doesn't match expected project ID
    """
    env = os.environ.get("ENV", "local").lower()
    project_id = os.environ.get("GCP_PROJECT_ID") or os.environ.get("FIREBASE_PROJECT_ID")
    
    # Skip validation for local development
    if env == "local":
        print("INFO: Local environment — deployment validation skipped.", file=sys.stderr)
        return
    
    # Validate ENV is recognized
    if env not in ("demo", "staging", "local", "prod"):
        raise DeploymentValidationError(
            f"Invalid ENV='{env}'. Must be one of: demo, staging, local, prod"
        )
    
    # Assert environment constraints
    if env == "demo":
        if project_id and project_id != EXPECTED_PROJECT_IDS["demo"]:
            raise DeploymentValidationError(
                f"FATAL: ENV=demo but PROJECT_ID='{project_id}' does not match expected "
                f"'{EXPECTED_PROJECT_IDS['demo']}'. This prevents accidental cross-deployment. "
                "Check your service account and env vars."
            )
        print(f"✓ Deployment validation passed: ENV={env}, PROJECT={project_id}", file=sys.stderr)
    
    elif env == "staging":
        if project_id and project_id != EXPECTED_PROJECT_IDS["staging"]:
            raise DeploymentValidationError(
                f"FATAL: ENV=staging but PROJECT_ID='{project_id}' does not match expected "
                f"'{EXPECTED_PROJECT_IDS['staging']}'. This prevents accidental cross-deployment. "
                "Check your service account and env vars."
            )
        print(f"✓ Deployment validation passed: ENV={env}, PROJECT={project_id}", file=sys.stderr)
    
    print(f"INFO: Startup assertion passed — ENV={env}, PROJECT={project_id}", file=sys.stderr)


class Environment(str, Enum):
    """Application environment."""
    LOCAL = "local"
    STAGING = "staging"
    DEMO = "demo"
    PROD = "prod"


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Environment variables take precedence over .env file.
    The .env file is only loaded in local environment.
    """
    
    # ===========================================
    # Core Settings
    # ===========================================
    ENV: Environment = Environment.LOCAL
    APP_NAME: str = "ResilAI"
    APP_VERSION: Optional[str] = None
    DEPLOYED_AT: Optional[str] = None
    DEBUG: bool = False
    
    # ===========================================
    # Server Settings
    # ===========================================
    PORT: int = 8000
    
    # ===========================================
    # Database
    # ===========================================
    DATABASE_URL: str = "sqlite:///./airs.db"
    
    # ===========================================
    # CORS Configuration
    # ===========================================
    # Comma-separated list of allowed origins
    # Example: "http://localhost:3000,https://myapp.com"
    # Use "*" to allow all origins (not recommended for production)
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173"
    
    # ===========================================
    # GCP Settings (Optional)
    # ===========================================
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: str = "us-central1"
    
    # ===========================================
    # Authentication
    # ===========================================
    AUTH_REQUIRED: bool = True  # Default secure: require Firebase auth
    FIREBASE_AUTH_EMULATOR_HOST: Optional[str] = None
    
    # ===========================================
    # Demo Mode
    # ===========================================
    # DEMO_MODE allows LLM features without strict production validation.
    # Use for CISO demos, sales presentations, and testing.
    # In demo mode:
    #   - AIRS_USE_LLM=true works without GEMINI_API_KEY validation
    #   - LLM generates narratives only (no score modification)
    #   - Falls back to deterministic text if LLM fails
    DEMO_MODE: bool = False
    INTEGRATIONS_ENABLED: bool = True
    
    # ===========================================
    # LLM Feature Flags
    # ===========================================
    # LLM is ONLY used for narrative text generation:
    #   - Executive summary paragraph
    #   - 30/60/90 day roadmap narrative
    # LLM does NOT modify:
    #   - Numeric scores (overall_score, domain_scores)
    #   - Maturity tier/level
    #   - Findings (severity, count, recommendations)
    AIRS_USE_LLM: bool = False
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-3-flash"
    GEMINI_MODEL: str = "gemini-3-flash"  # Alias for backwards compatibility
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.7
    
    # ===========================================
    # Implementation Assistance Mode
    # ===========================================
    # When enabled, LLM-generated narratives include direct implementation
    # guide links from CISA, NIST, and OWASP in remediation priorities.
    # When disabled (default), links are omitted to preserve consulting
    # upsell positioning — clients receive actionable recommendations
    # without self-service resource pointers.
    IMPLEMENTATION_ASSISTANCE_MODE: bool = False

    # ===========================================
    # Field-Level Encryption (AES-256-GCM)
    # ===========================================
    # Base64-encoded 32-byte key for encrypting sensitive org fields
    # in Firestore.  When unset, encryption runs in passthrough mode.
    # Generate a key:
    #   python -c "from app.core.security.encryption import generate_encryption_key; print(generate_encryption_key())"
    ENCRYPTION_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        case_sensitive=True,
        # env_file is set dynamically in settings_customise_sources
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate that production environment has required settings."""
        errors = []
        
        if self.ENV in (Environment.PROD, Environment.STAGING):
            # SECURITY: DEMO_MODE must never be enabled in prod/staging
            if self.DEMO_MODE:
                errors.append(
                    f"DEMO_MODE=true is FORBIDDEN in {self.ENV.value}. "
                    "It disables authentication. Set DEMO_MODE=false."
                )

            # In production, CORS wildcard is now blocked by cors.py
            # Just log a warning here for visibility
            if self.CORS_ALLOW_ORIGINS == "*":
                print(
                    "ERROR: CORS_ALLOW_ORIGINS='*' is blocked in production. "
                    "Set specific origins in CORS_ALLOW_ORIGINS.",
                    file=sys.stderr
                )
            
            # In production with LLM enabled, either API key or ADC should exist
            if self.AIRS_USE_LLM and not self.GEMINI_API_KEY and not self.GCP_PROJECT_ID:
                print(
                    "WARNING: AIRS_USE_LLM=true but neither GEMINI_API_KEY nor GCP_PROJECT_ID is set.",
                    file=sys.stderr
                )
        
        # Demo mode warnings (local only)
        if self.DEMO_MODE:
            print(
                "INFO: DEMO_MODE=true (local). LLM features enabled for demonstration purposes.",
                file=sys.stderr
            )
            if self.AIRS_USE_LLM:
                print(
                    "INFO: LLM running in demo mode - generates narratives only, no score modification.",
                    file=sys.stderr
                )
        
        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + 
                "\n".join(f"  - {e}" for e in errors)
            )
        
        return self

    @field_validator("CORS_ALLOW_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if not v or not v.strip():
            raise ValueError("CORS_ALLOW_ORIGINS cannot be empty")
        return v.strip()

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL is provided."""
        if not v or not v.strip():
            raise ValueError("DATABASE_URL is required")
        return v.strip()

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Get validated CORS origins list.
        
        Uses the cors module for validation:
        - Validates scheme (http/https)
        - Validates hostname format
        - Rejects malformed origins with warnings
        - Blocks wildcard '*' in production
        """
        from app.core.cors import get_allowed_origins
        return get_allowed_origins(
            env_var="CORS_ALLOW_ORIGINS",
            default=self.CORS_ALLOW_ORIGINS,
            is_production=self.is_prod
        )

    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.ENV == Environment.LOCAL

    @property
    def is_prod(self) -> bool:
        """Check if running in production-like environment (demo, staging, or prod)."""
        return self.ENV in (Environment.PROD, Environment.STAGING, Environment.DEMO)

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENV == Environment.STAGING

    @property
    def is_auth_required(self) -> bool:
        """Check if authentication is required for protected endpoints.
        
        Auth is required when AUTH_REQUIRED=true OR in prod/staging.
        DEMO_MODE no longer bypasses auth — it only enables LLM features.
        """
        return self.AUTH_REQUIRED or self.ENV in (Environment.PROD, Environment.STAGING)

    @property
    def is_llm_enabled(self) -> bool:
        """
        Check if LLM narrative generation is enabled.
        
        LLM is enabled when:
          - AIRS_USE_LLM=true AND one of:
            - DEMO_MODE=true
            - GEMINI_API_KEY is set (direct API-key auth)
            - GCP_PROJECT_ID is set (Vertex/ADC auth)
        
        In demo mode, LLM can run without strict API key validation,
        using ADC (Application Default Credentials) on Cloud Run.
        
        Note: LLM only generates narrative text. It does NOT modify:
          - Numeric scores (overall_score, domain_scores)
          - Maturity tier/level  
          - Findings (severity, recommendations)
        """
        if not self.AIRS_USE_LLM:
            return False
        # In demo mode, allow LLM even without explicit API key (use ADC/fallback)
        if self.DEMO_MODE:
            return True
        # Non-demo mode supports either API key auth or Vertex/ADC auth.
        return bool(self.GEMINI_API_KEY or self.GCP_PROJECT_ID)

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode for presentations/testing."""
        return self.DEMO_MODE or self.ENV == Environment.DEMO
    
    @property
    def is_read_only(self) -> bool:
        """
        Check if the environment is read-only (demo mode).
        
        In demo mode, all write operations are blocked to prevent
        accidental data corruption during investor demos or presentations.
        """
        return self.ENV == Environment.DEMO


def _load_env_file() -> Optional[str]:
    """
    Determine if .env file should be loaded.
    
    In local mode, prefer .env.dev when present, then fall back to .env.
    """
    # Check ENV from environment first
    env_value = os.environ.get("ENV", "local").lower()
    
    if env_value == "local":
        if os.path.exists(".env.dev"):
            return ".env.dev"
        if os.path.exists(".env"):
            return ".env"
    return None


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    env_file = _load_env_file()
    
    if env_file:
        # Load .env file for local development
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # python-dotenv not installed, rely on pydantic-settings
            pass
    
    return Settings(_env_file=env_file)


# Create settings instance for backward compatibility
# Note: This will validate on import
try:
    settings = get_settings()
except Exception as e:
    print(f"ERROR: Failed to load configuration: {e}", file=sys.stderr)
    raise


# Export environment enum for type hints
__all__ = [
    "Settings", 
    "Environment", 
    "settings", 
    "get_settings",
    "DeploymentValidationError",
    "validate_deployment",
    "EXPECTED_PROJECT_IDS",
]

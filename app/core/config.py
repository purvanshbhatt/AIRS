"""
AIRS Configuration Module

Uses pydantic-settings for type-safe configuration with validation.
Loads .env file only in local environment mode.
"""

import os
import sys
from enum import Enum
from typing import Optional, List
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""
    LOCAL = "local"
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
    APP_NAME: str = "AIRS"
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
    CORS_ALLOW_ORIGINS: str = "*"
    
    # ===========================================
    # GCP Settings (Optional)
    # ===========================================
    GCP_PROJECT_ID: Optional[str] = None
    
    # ===========================================
    # Authentication
    # ===========================================
    AUTH_REQUIRED: bool = False  # Set to true to require Firebase auth
    
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
    LLM_MODEL: str = "gemini-3.0-pro"
    GEMINI_MODEL: str = "gemini-3.0-pro"  # Alias for backwards compatibility
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.7

    # ===========================================
    # Report Storage Configuration
    # ===========================================
    # Storage mode: "local" for development, "gcs" for production (Google Cloud Storage)
    REPORTS_STORAGE_MODE: str = "local"
    # GCS bucket name (required when REPORTS_STORAGE_MODE=gcs)
    GCS_BUCKET_NAME: Optional[str] = None
    # Local directory for PDF storage (when REPORTS_STORAGE_MODE=local)
    LOCAL_REPORTS_DIR: str = "./generated_reports"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        # env_file is set dynamically in settings_customise_sources
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate that production environment has required settings."""
        errors = []
        
        if self.ENV == Environment.PROD:
            # In production, CORS wildcard is now blocked by cors.py
            # Just log a warning here for visibility
            if self.CORS_ALLOW_ORIGINS == "*":
                print(
                    "ERROR: CORS_ALLOW_ORIGINS='*' is blocked in production. "
                    "Set specific origins in CORS_ALLOW_ORIGINS.",
                    file=sys.stderr
                )
            
            # In production with LLM enabled (not demo mode), API key is recommended
            if self.AIRS_USE_LLM and not self.GEMINI_API_KEY and not self.DEMO_MODE:
                print(
                    "INFO: GEMINI_API_KEY not set. Using Application Default Credentials for Gemini.",
                    file=sys.stderr
                )
            
            # Validate GCS configuration in production
            if self.REPORTS_STORAGE_MODE == "gcs" and not self.GCS_BUCKET_NAME:
                errors.append("GCS_BUCKET_NAME is required when REPORTS_STORAGE_MODE=gcs")
        
        # Validate storage mode value
        if self.REPORTS_STORAGE_MODE not in ("local", "gcs"):
            errors.append(f"REPORTS_STORAGE_MODE must be 'local' or 'gcs', got: {self.REPORTS_STORAGE_MODE}")
        
        # Demo mode warnings
        if self.DEMO_MODE:
            print(
                "WARNING: DEMO_MODE=true. LLM features enabled for demonstration purposes.",
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
        """Check if running in production environment."""
        return self.ENV == Environment.PROD

    @property
    def is_auth_required(self) -> bool:
        """Check if authentication is required for protected endpoints."""
        return self.AUTH_REQUIRED or self.ENV == Environment.PROD

    @property
    def is_llm_enabled(self) -> bool:
        """
        Check if LLM narrative generation is enabled.
        
        LLM is enabled when:
          - AIRS_USE_LLM=true AND (GEMINI_API_KEY is set OR DEMO_MODE=true)
        
        In demo mode, LLM can run without strict API key validation,
        using ADC (Application Default Credentials) on Cloud Run.
        
        Note: LLM only generates narrative text. It does NOT modify:
          - Numeric scores (overall_score, domain_scores)
          - Maturity tier/level  
          - Findings (severity, recommendations)
        """
        if not self.AIRS_USE_LLM:
            return False
        # In demo mode, allow LLM even without explicit API key (use ADC)
        if self.DEMO_MODE:
            return True
        # Otherwise require API key
        return bool(self.GEMINI_API_KEY)

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode for presentations/testing."""
        return self.DEMO_MODE

    @property
    def is_gcs_storage(self) -> bool:
        """Check if using GCS for report storage."""
        return self.REPORTS_STORAGE_MODE == "gcs"


def _load_env_file() -> Optional[str]:
    """
    Determine if .env file should be loaded.
    
    Only loads .env in local mode or if ENV is not set.
    """
    # Check ENV from environment first
    env_value = os.environ.get("ENV", "local").lower()
    
    if env_value == "local" and os.path.exists(".env"):
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
    
    return Settings(_env_file=env_file if env_file else None)


# Create settings instance for backward compatibility
# Note: This will validate on import
try:
    settings = get_settings()
except Exception as e:
    print(f"ERROR: Failed to load configuration: {e}", file=sys.stderr)
    raise


# Export environment enum for type hints
__all__ = ["Settings", "Environment", "settings", "get_settings"]

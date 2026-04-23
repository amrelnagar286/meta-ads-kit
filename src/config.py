"""
Configuration Management — Centralized config with environment variable support.
Loads from .env files and provides typed access to all settings.
"""
import os
from pathlib import Path


def load_env_file(path: str = ".env") -> None:
    """Load environment variables from a .env file."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


load_env_file()


class Config:
    """Centralized application configuration."""

    # Meta API Credentials
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")
    META_AD_ACCOUNT_ID: str = os.getenv("META_AD_ACCOUNT_ID", "")
    META_API_VERSION: str = os.getenv("META_API_VERSION", "v25.0")

    # Application Settings
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    # Rate Limiting
    RATE_LIMIT_CALLS_PER_HOUR: int = int(os.getenv("RATE_LIMIT_CALLS_PER_HOUR", "180"))
    RATE_LIMIT_BATCH_SIZE: int = 50
    RATE_LIMIT_RETRY_MAX: int = 5
    RATE_LIMIT_BACKOFF_BASE: float = 2.0

    # Data & Caching
    DATA_DIR: str = str(Path(__file__).parent.parent / "data")
    CACHE_TTL_SECONDS: int = 300
    INSIGHTS_CACHE_TTL: int = 900

    # Bulk Operations
    BULK_MAX_ROWS: int = 10000
    BULK_TEMPLATE_DIR: str = str(Path(__file__).parent.parent / "templates")
    BULK_DRY_RUN_DEFAULT: bool = True

    # Automation
    AUTOMATION_CHECK_INTERVAL: int = 300
    AUTOMATION_MAX_RULES: int = 100
    STOP_LOSS_DEFAULT_PERCENT: float = 50.0

    # Core Metrics
    CORE_METRICS: list = [
        "spend", "impressions", "clicks", "ctr",
        "cost_per_action_type", "actions", "conversions",
        "cost_per_conversion", "purchase_roas", "reach", "frequency",
    ]

    PERFORMANCE_METRICS: list = [
        "spend", "impressions", "clicks", "ctr", "conversions",
        "cost_per_conversion", "purchase_roas", "reach", "frequency",
    ]

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.META_ACCESS_TOKEN and cls.META_AD_ACCOUNT_ID)

    @classmethod
    def get_ad_account_id_clean(cls) -> str:
        aid = cls.META_AD_ACCOUNT_ID
        if aid and not aid.startswith("act_"):
            return f"act_{aid}"
        return aid

    @classmethod
    def update(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)


config = Config()

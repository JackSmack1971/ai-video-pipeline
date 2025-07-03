import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SecureConfig:
    @staticmethod
    def get_secret(secret_name: str) -> str:
        """Securely load secrets from Docker secrets or environment files."""
        # Priority 1: Docker secret file
        secret_file = f"/run/secrets/{secret_name}"
        if os.path.exists(secret_file):
            try:
                value = Path(secret_file).read_text().strip()
                logger.info("Loaded secret from Docker secrets")
                return value
            except Exception as e:
                logger.error("Failed to read Docker secret")
        # Priority 2: Environment variable pointing to file
        env_file_var = f"{secret_name.upper()}_FILE"
        if env_file_var in os.environ:
            try:
                file_path = os.environ[env_file_var]
                value = Path(file_path).read_text().strip()
                logger.info("Loaded secret from file")
                return value
            except Exception as e:
                logger.error("Failed to read secret file")
        # Priority 3: Direct environment variable (fallback, less secure)
        env_value = os.getenv(secret_name.upper())
        if env_value:
            logger.warning(
                "Using direct environment variable; consider Docker secrets"
            )
            return env_value
        logger.error("Secret not found in any location")
        return ""

    @staticmethod
    def get_required_secret(secret_name: str) -> str:
        """Get a required secret, raise exception if not found."""
        value = SecureConfig.get_secret(secret_name)
        if not value:
            raise ValueError("Required secret not found")
        return value

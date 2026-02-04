"""
Production Environment Validation Script
Validates all required environment variables before deployment

Usage:
    python validate_production_env.py --env-file .env.production
"""

import os
import sys
import re
from typing import List, Tuple, Dict
from pathlib import Path
import argparse


class Colors:
    """ANSI color codes"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


class EnvironmentValidator:
    """Validates production environment configuration"""

    # Required environment variables
    REQUIRED_VARS = {
        # Security (Critical)
        "SECRET_KEY": {"min_length": 32, "type": "secret"},
        "JWT_SECRET_KEY": {"min_length": 32, "type": "secret"},
        "ENCRYPTION_KEY": {"min_length": 32, "type": "secret"},
        # Database
        "DATABASE_URL": {"pattern": r"postgresql\+asyncpg://.*", "type": "url"},
        # Redis
        "REDIS_URL": {"pattern": r"redis://.*", "type": "url"},
        # External APIs
        "YOUTUBE_API_KEY_1": {"min_length": 20, "type": "api_key"},
        "OPENAI_API_KEY": {"min_length": 20, "type": "api_key"},
        # Monitoring
        "SENTRY_DSN": {
            "pattern": r"https://.*@.*\.ingest\.sentry\.io/.*",
            "type": "url",
        },
        # CORS
        "CORS_ORIGINS": {"type": "list"},
    }

    # Optional but recommended
    RECOMMENDED_VARS = [
        "DATABASE_READ_REPLICA_URL",
        "YOUTUBE_API_KEY_2",
        "YOUTUBE_API_KEY_3",
        "ELASTICSEARCH_URL",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "SMTP_HOST",
    ]

    # Variables that should NOT contain placeholders
    PLACEHOLDER_PATTERNS = [
        r"<REPLACE.*?>",
        r"<.*_KEY.*?>",
        r"<.*_PASSWORD.*?>",
        r"<AUTO_FILLED.*?>",
        r"CHANGE_ME",
        r"YOUR_.*_HERE",
    ]

    def __init__(self, env_file: str):
        self.env_file = Path(env_file)
        self.env_vars: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_env_file(self) -> bool:
        """Load .env file"""
        if not self.env_file.exists():
            self.errors.append(f"Environment file not found: {self.env_file}")
            return False

        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        self.env_vars[key] = value

            print_success(f"Loaded {len(self.env_vars)} variables from {self.env_file}")
            return True

        except Exception as e:
            self.errors.append(f"Failed to load env file: {str(e)}")
            return False

    def validate_required_vars(self):
        """Validate all required variables"""
        print_info("\n=== Validating Required Variables ===")

        for var_name, rules in self.REQUIRED_VARS.items():
            value = self.env_vars.get(var_name)

            if not value:
                self.errors.append(f"Missing required variable: {var_name}")
                print_error(f"{var_name}: Missing")
                continue

            # Check for placeholders
            if self._contains_placeholder(value):
                self.errors.append(f"{var_name} contains placeholder: {value}")
                print_error(f"{var_name}: Contains placeholder")
                continue

            # Validate min length
            if "min_length" in rules and len(value) < rules["min_length"]:
                self.errors.append(
                    f"{var_name} too short: {len(value)} chars (min: {rules['min_length']})"
                )
                print_error(
                    f"{var_name}: Too short ({len(value)} < {rules['min_length']})"
                )
                continue

            # Validate pattern
            if "pattern" in rules and not re.match(rules["pattern"], value):
                self.errors.append(
                    f"{var_name} doesn't match pattern: {rules['pattern']}"
                )
                print_error(f"{var_name}: Invalid format")
                continue

            # Validate type
            var_type = rules.get("type", "string")
            if var_type == "url" and not value.startswith(
                ("http://", "https://", "redis://", "postgresql")
            ):
                self.warnings.append(f"{var_name} doesn't look like a valid URL")
                print_warning(f"{var_name}: URL format suspicious")
            elif var_type == "list" and not (
                value.startswith("[") and value.endswith("]")
            ):
                self.warnings.append(f"{var_name} should be a list/array format")
                print_warning(f"{var_name}: Not in list format")

            # Success
            masked_value = self._mask_sensitive(value, var_name)
            print_success(f"{var_name}: {masked_value}")

    def validate_recommended_vars(self):
        """Check recommended variables"""
        print_info("\n=== Checking Recommended Variables ===")

        for var_name in self.RECOMMENDED_VARS:
            value = self.env_vars.get(var_name)

            if not value:
                self.warnings.append(f"Recommended variable missing: {var_name}")
                print_warning(f"{var_name}: Not set (recommended)")
            elif self._contains_placeholder(value):
                self.warnings.append(f"{var_name} contains placeholder")
                print_warning(f"{var_name}: Contains placeholder")
            else:
                masked_value = self._mask_sensitive(value, var_name)
                print_success(f"{var_name}: {masked_value}")

    def validate_security(self):
        """Security-specific validations"""
        print_info("\n=== Security Checks ===")

        # Check SECRET_KEY randomness
        secret_key = self.env_vars.get("SECRET_KEY", "")
        if secret_key:
            if len(set(secret_key)) < 16:
                self.warnings.append("SECRET_KEY has low entropy (not random enough)")
                print_warning("SECRET_KEY: Low entropy detected")
            else:
                print_success("SECRET_KEY: Good entropy")

        # Check JWT_SECRET_KEY is different from SECRET_KEY
        jwt_secret = self.env_vars.get("JWT_SECRET_KEY", "")
        if secret_key and jwt_secret and secret_key == jwt_secret:
            self.errors.append("JWT_SECRET_KEY must be different from SECRET_KEY")
            print_error("SECRET_KEY == JWT_SECRET_KEY (should be different)")
        else:
            print_success("JWT_SECRET_KEY: Different from SECRET_KEY")

        # Check DEBUG mode
        debug = self.env_vars.get("DEBUG", "false").lower()
        if debug == "true":
            self.errors.append("DEBUG=true in production! Must be false")
            print_error("DEBUG: Enabled (MUST be false in production)")
        else:
            print_success("DEBUG: Disabled")

        # Check ENVIRONMENT
        env = self.env_vars.get("ENVIRONMENT", "").lower()
        if env != "production":
            self.warnings.append(f"ENVIRONMENT={env} (expected 'production')")
            print_warning(f"ENVIRONMENT: {env} (should be 'production')")
        else:
            print_success("ENVIRONMENT: production")

    def validate_database(self):
        """Database-specific validations"""
        print_info("\n=== Database Configuration ===")

        db_url = self.env_vars.get("DATABASE_URL", "")
        if "localhost" in db_url or "127.0.0.1" in db_url:
            self.warnings.append("DATABASE_URL points to localhost (not production?)")
            print_warning("DATABASE_URL: Points to localhost")
        else:
            print_success("DATABASE_URL: Remote database")

        # Check pool size
        pool_size = self.env_vars.get("DATABASE_POOL_SIZE", "20")
        try:
            pool_size_int = int(pool_size)
            if pool_size_int < 10:
                self.warnings.append(
                    f"DATABASE_POOL_SIZE={pool_size_int} might be too small"
                )
                print_warning(f"DATABASE_POOL_SIZE: {pool_size_int} (consider 20+)")
            else:
                print_success(f"DATABASE_POOL_SIZE: {pool_size_int}")
        except ValueError:
            self.errors.append(f"DATABASE_POOL_SIZE is not a number: {pool_size}")
            print_error(f"DATABASE_POOL_SIZE: Invalid ({pool_size})")

    def validate_api_keys(self):
        """Validate external API keys"""
        print_info("\n=== External API Keys ===")

        # YouTube API
        youtube_keys = [k for k in self.env_vars if k.startswith("YOUTUBE_API_KEY")]
        if len(youtube_keys) < 2:
            self.warnings.append(
                "Only 1 YouTube API key (recommend 3 for quota management)"
            )
            print_warning(f"YouTube API Keys: {len(youtube_keys)} (recommend 3)")
        else:
            print_success(f"YouTube API Keys: {len(youtube_keys)} configured")

        # OpenAI
        openai_key = self.env_vars.get("OPENAI_API_KEY", "")
        if openai_key and openai_key.startswith("sk-"):
            print_success("OpenAI API Key: Valid format")
        elif openai_key:
            self.warnings.append("OpenAI API key doesn't start with 'sk-'")
            print_warning("OpenAI API Key: Unusual format")

        # HuggingFace
        hf_token = self.env_vars.get("HUGGINGFACE_API_TOKEN", "")
        if not hf_token:
            self.warnings.append("HUGGINGFACE_API_TOKEN not set (BERTurk won't work)")
            print_warning("HuggingFace Token: Not set")

    def validate_cors(self):
        """Validate CORS configuration"""
        print_info("\n=== CORS Configuration ===")

        cors_origins = self.env_vars.get("CORS_ORIGINS", "")
        if "localhost" in cors_origins or "127.0.0.1" in cors_origins:
            self.warnings.append("CORS_ORIGINS includes localhost (development?)")
            print_warning("CORS_ORIGINS: Includes localhost")

        if cors_origins == '["*"]':
            self.errors.append("CORS_ORIGINS allows all origins (*) - security risk!")
            print_error("CORS_ORIGINS: Wildcard (*) not allowed in production")
        else:
            print_success("CORS_ORIGINS: Properly restricted")

    def _contains_placeholder(self, value: str) -> bool:
        """Check if value contains placeholder text"""
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def _mask_sensitive(self, value: str, var_name: str) -> str:
        """Mask sensitive values for display"""
        sensitive_keywords = ["key", "secret", "password", "token", "dsn"]

        if any(kw in var_name.lower() for kw in sensitive_keywords):
            if len(value) > 8:
                return f"{value[:4]}...{value[-4:]}"
            else:
                return "***"

        # For URLs, mask passwords
        if "://" in value and "@" in value:
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", value)

        return value

    def generate_secrets(self):
        """Generate example secure secrets"""
        print_info("\n=== Secret Generation Examples ===")
        print("\nTo generate secure secrets, run:")
        print(
            f'{Colors.BOLD}python -c "import secrets; print(secrets.token_urlsafe(32))"{Colors.END}'
        )
        print("\nFor Fernet encryption key:")
        print(
            f'{Colors.BOLD}python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"{Colors.END}'
        )

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.END}")
        print("=" * 70)

        total_vars = len(self.env_vars)
        required_ok = len(self.REQUIRED_VARS) - len(
            [e for e in self.errors if "Missing required" in e]
        )

        print(f"\nTotal Variables: {total_vars}")
        print(f"Required Variables: {required_ok}/{len(self.REQUIRED_VARS)} ✓")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS (Must Fix):{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS (Recommended):{Colors.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        print("\n" + "=" * 70)

        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}❌ VALIDATION FAILED{Colors.END}")
            print(f"Fix {len(self.errors)} error(s) before deploying to production!")
            return False
        elif self.warnings:
            print(
                f"{Colors.YELLOW}{Colors.BOLD}⚠ VALIDATION PASSED WITH WARNINGS{Colors.END}"
            )
            print(
                f"Consider fixing {len(self.warnings)} warning(s) for best practices."
            )
            return True
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ VALIDATION PASSED{Colors.END}")
            print("Environment configuration is production-ready!")
            return True

    def run(self) -> bool:
        """Run all validations"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(
            f"{Colors.BOLD}YKS HAZIRLIK PLATFORMU - PRODUCTION ENVIRONMENT VALIDATION{Colors.END}"
        )
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")

        if not self.load_env_file():
            return False

        self.validate_required_vars()
        self.validate_recommended_vars()
        self.validate_security()
        self.validate_database()
        self.validate_api_keys()
        self.validate_cors()

        self.generate_secrets()

        return self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Validate production environment configuration"
    )
    parser.add_argument(
        "--env-file",
        default=".env.production",
        help="Path to .env file (default: .env.production)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    args = parser.parse_args()

    validator = EnvironmentValidator(args.env_file)
    success = validator.run()

    # Exit with error code if validation failed
    if not success or (args.strict and validator.warnings):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

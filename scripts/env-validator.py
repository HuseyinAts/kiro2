#!/usr/bin/env python3
"""
KIRO2 Environment Variable Validator
Production ortam değişkenlerini kontrol eder
"""

import os
import re
import sys
from typing import Dict, List, Optional, Tuple, Union


class ColorOutput:
    """Console color output helper"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @classmethod
    def print_colored(cls, text: str, color: str = None, bold: bool = False):
        """Print colored text to console"""
        colors = {
            'red': cls.RED,
            'green': cls.GREEN,
            'yellow': cls.YELLOW,
            'blue': cls.BLUE,
            'purple': cls.PURPLE,
            'cyan': cls.CYAN,
            'white': cls.WHITE
        }
        
        prefix = ""
        if bold:
            prefix += cls.BOLD
        if color and color.lower() in colors:
            prefix += colors[color.lower()]
            
        print(f"{prefix}{text}{cls.END}")


class ValidationRule:
    """Environment variable validation rule"""
    
    def __init__(self, name: str, required: bool = True, pattern: str = None, 
                 min_length: int = None, max_length: int = None, 
                 description: str = "", security_level: str = "medium"):
        self.name = name
        self.required = required
        self.pattern = pattern
        self.min_length = min_length
        self.max_length = max_length
        self.description = description
        self.security_level = security_level  # low, medium, high, critical


class EnvironmentValidator:
    """Environment variables validator for KIRO2"""
    
    def __init__(self, env_file_path: str = ".env.production"):
        self.env_file_path = env_file_path
        self.env_vars = {}
        self.errors = []
        self.warnings = []
        self.security_issues = []
        
        # Define validation rules
        self.validation_rules = [
            # Application Configuration
            ValidationRule("APP_NAME", required=True, min_length=3, 
                          description="Application name"),
            ValidationRule("ENVIRONMENT", required=True, pattern=r"^production$", 
                          description="Environment must be 'production'"),
            ValidationRule("DEBUG", required=True, pattern=r"^false$", 
                          description="DEBUG must be false in production"),
            ValidationRule("LOG_LEVEL", required=True, pattern=r"^(INFO|WARN|ERROR)$", 
                          description="Log level for production"),
            
            # Security Configuration - CRITICAL
            ValidationRule("SECRET_KEY", required=True, min_length=32, 
                          description="Application secret key", security_level="critical"),
            ValidationRule("JWT_SECRET_KEY", required=True, min_length=32, 
                          description="JWT secret key", security_level="critical"),
            ValidationRule("JWT_ALGORITHM", required=True, pattern=r"^HS256$", 
                          description="JWT algorithm"),
            
            # Database Configuration
            ValidationRule("DATABASE_URL", required=True, pattern=r"^postgresql.*://.*", 
                          description="PostgreSQL connection URL", security_level="high"),
            ValidationRule("POSTGRES_PASSWORD", required=True, min_length=12, 
                          description="PostgreSQL password", security_level="high"),
            ValidationRule("DATABASE_MAX_CONNECTIONS", pattern=r"^\d+$", 
                          description="Max database connections"),
            
            # Redis Configuration
            ValidationRule("REDIS_URL", required=True, pattern=r"^redis://.*", 
                          description="Redis connection URL"),
            ValidationRule("REDIS_PASSWORD", required=True, min_length=8, 
                          description="Redis password", security_level="high"),
            
            # Elasticsearch
            ValidationRule("ELASTICSEARCH_URL", required=True, pattern=r"^https?://.*", 
                          description="Elasticsearch URL"),
            
            # Email Configuration
            ValidationRule("SMTP_HOST", required=True, 
                          description="SMTP server host"),
            ValidationRule("SMTP_PORT", required=True, pattern=r"^(25|587|465)$", 
                          description="SMTP server port"),
            ValidationRule("SMTP_USERNAME", required=True, 
                          description="SMTP username"),
            ValidationRule("SMTP_PASSWORD", required=True, min_length=8, 
                          description="SMTP password", security_level="high"),
            
            # SSL/TLS Configuration  
            ValidationRule("SSL_ENABLED", required=True, pattern=r"^true$", 
                          description="SSL must be enabled in production"),
            ValidationRule("SSL_CERT_PATH", required=False, 
                          description="SSL certificate path"),
            ValidationRule("SSL_KEY_PATH", required=False, 
                          description="SSL private key path"),
            
            # Monitoring
            ValidationRule("SENTRY_DSN", required=False, pattern=r"^https://.*@sentry\.io/.*", 
                          description="Sentry DSN for error tracking"),
            ValidationRule("GRAFANA_ADMIN_PASSWORD", required=True, min_length=8, 
                          description="Grafana admin password", security_level="medium"),
            ValidationRule("GRAFANA_SECRET_KEY", required=True, min_length=16, 
                          description="Grafana secret key", security_level="medium"),
            
            # Security Headers
            ValidationRule("SECURITY_HEADERS_ENABLED", required=True, pattern=r"^true$", 
                          description="Security headers must be enabled"),
            ValidationRule("HSTS_MAX_AGE", pattern=r"^\d+$", 
                          description="HSTS max age in seconds"),
            
            # Turkish Localization
            ValidationRule("DEFAULT_LANGUAGE", pattern=r"^tr_TR$", 
                          description="Default language for Turkish"),
            ValidationRule("TIMEZONE", pattern=r"^Europe/Istanbul$", 
                          description="Timezone for Turkey"),
            
            # Performance
            ValidationRule("WORKER_PROCESSES", pattern=r"^[1-8]$", 
                          description="Number of worker processes"),
            ValidationRule("CACHE_ENABLED", required=True, pattern=r"^true$", 
                          description="Cache must be enabled in production"),
            
            # Backup Configuration
            ValidationRule("BACKUP_ENABLED", required=True, pattern=r"^true$", 
                          description="Backup must be enabled in production"),
            ValidationRule("BACKUP_S3_BUCKET", required=False, 
                          description="S3 bucket for backups"),
        ]
    
    def load_env_file(self) -> bool:
        """Load environment variables from file"""
        try:
            if not os.path.exists(self.env_file_path):
                ColorOutput.print_colored(f"[X] Environment file not found: {self.env_file_path}", "red", bold=True)
                return False
            
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self.env_vars[key] = value
                    else:
                        self.warnings.append(f"Line {line_num}: Invalid format: {line}")
            
            ColorOutput.print_colored(f"[CHECK] Loaded {len(self.env_vars)} environment variables from {self.env_file_path}", "green")
            return True
            
        except Exception as e:
            ColorOutput.print_colored(f"[X] Error loading environment file: {e}", "red", bold=True)
            return False
    
    def validate_rule(self, rule: ValidationRule) -> bool:
        """Validate a single environment variable rule"""
        value = self.env_vars.get(rule.name)
        is_valid = True
        
        # Check if required variable exists
        if rule.required and not value:
            self.errors.append(f"[X] REQUIRED: {rule.name} is required but not set")
            if rule.description:
                self.errors.append(f"   Description: {rule.description}")
            return False
        
        # Skip validation if optional and not set
        if not rule.required and not value:
            return True
        
        # Pattern validation
        if rule.pattern and value:
            if not re.match(rule.pattern, value):
                self.errors.append(f"[X] PATTERN: {rule.name}='{value}' does not match pattern: {rule.pattern}")
                if rule.description:
                    self.errors.append(f"   Description: {rule.description}")
                is_valid = False
        
        # Length validation
        if value:
            if rule.min_length and len(value) < rule.min_length:
                self.errors.append(f"[X] LENGTH: {rule.name} must be at least {rule.min_length} characters long")
                is_valid = False
            
            if rule.max_length and len(value) > rule.max_length:
                self.errors.append(f"[X] LENGTH: {rule.name} must be at most {rule.max_length} characters long")
                is_valid = False
        
        # Security validation
        if value and rule.security_level in ['high', 'critical']:
            self._check_security_issues(rule.name, value, rule.security_level)
        
        return is_valid
    
    def _check_security_issues(self, var_name: str, value: str, level: str):
        """Check for common security issues"""
        # Check for weak passwords
        if any(keyword in var_name.lower() for keyword in ['password', 'secret', 'key', 'token']):
            issues = []
            
            if len(value) < 12:
                issues.append("too short")
            
            if value.lower() in ['password', '123456', 'admin', 'root', 'test']:
                issues.append("common weak value")
            
            if value.isdigit():
                issues.append("only numbers")
            
            if value.isalpha():
                issues.append("only letters")
            
            if not re.search(r'[A-Z]', value):
                issues.append("no uppercase letters")
            
            if not re.search(r'[a-z]', value):
                issues.append("no lowercase letters")
            
            if not re.search(r'[0-9]', value):
                issues.append("no numbers")
            
            if not re.search(r'[^A-Za-z0-9]', value):
                issues.append("no special characters")
            
            if issues:
                security_level = "🔴 CRITICAL" if level == "critical" else "🟡 HIGH"
                self.security_issues.append(f"{security_level}: {var_name} has security issues: {', '.join(issues)}")
    
    def check_production_readiness(self):
        """Check if configuration is production ready"""
        production_checks = [
            ("DEBUG", "false", "Debug mode must be disabled"),
            ("ENVIRONMENT", "production", "Environment must be set to production"),
            ("SSL_ENABLED", "true", "SSL must be enabled"),
            ("SECURITY_HEADERS_ENABLED", "true", "Security headers must be enabled"),
            ("CACHE_ENABLED", "true", "Cache must be enabled"),
            ("BACKUP_ENABLED", "true", "Backup must be enabled"),
        ]
        
        for var_name, expected_value, description in production_checks:
            actual_value = self.env_vars.get(var_name, "").lower()
            expected_lower = expected_value.lower()
            
            if actual_value != expected_lower:
                self.errors.append(f"[X] PRODUCTION: {var_name} should be '{expected_value}' in production (current: '{actual_value}')")
                self.errors.append(f"   Reason: {description}")
    
    def check_turkish_configuration(self):
        """Check Turkish-specific configuration"""
        turkish_checks = [
            ("DEFAULT_LANGUAGE", "tr_TR", "Default language should be Turkish"),
            ("TIMEZONE", "Europe/Istanbul", "Timezone should be Turkey timezone"),
            ("CURRENCY", "TRY", "Currency should be Turkish Lira"),
        ]
        
        for var_name, expected_value, description in turkish_checks:
            actual_value = self.env_vars.get(var_name, "")
            
            if actual_value != expected_value:
                self.warnings.append(f"⚠️  TURKISH: {var_name} should be '{expected_value}' for Turkish users (current: '{actual_value}')")
                self.warnings.append(f"   Reason: {description}")
    
    def validate_database_url(self):
        """Validate database URL format and security"""
        db_url = self.env_vars.get("DATABASE_URL", "")
        
        if db_url:
            # Check if password is in URL (security risk)
            if "@" in db_url and ":" in db_url.split("@")[0]:
                self.security_issues.append("🟡 MEDIUM: Database password in connection URL. Consider using separate PASSWORD env var")
            
            # Check for localhost/127.0.0.1 in production
            if "localhost" in db_url or "127.0.0.1" in db_url:
                self.warnings.append("⚠️  DATABASE: Using localhost in DATABASE_URL may not work in containerized environment")
    
    def validate_all(self) -> bool:
        """Run all validations"""
        ColorOutput.print_colored("\n[MAG] KIRO2 Production Environment Validation", "cyan", bold=True)
        ColorOutput.print_colored("=" * 50, "cyan")
        
        # Load environment file
        if not self.load_env_file():
            return False
        
        ColorOutput.print_colored(f"\n[CLIPBOARD] Validating {len(self.validation_rules)} rules...", "blue")
        
        # Validate each rule
        valid_count = 0
        for rule in self.validation_rules:
            if self.validate_rule(rule):
                valid_count += 1
        
        # Additional checks
        self.check_production_readiness()
        self.check_turkish_configuration()
        self.validate_database_url()
        
        # Print results
        self._print_results()
        
        # Return True if no critical errors
        return len(self.errors) == 0
    
    def _print_results(self):
        """Print validation results"""
        ColorOutput.print_colored(f"\n[CHART] Validation Results", "blue", bold=True)
        ColorOutput.print_colored("-" * 30, "blue")
        
        # Summary
        total_rules = len(self.validation_rules)
        valid_rules = total_rules - len([e for e in self.errors if "[X]" in e])
        
        ColorOutput.print_colored(f"[CHECK] Valid rules: {valid_rules}/{total_rules}", "green")
        ColorOutput.print_colored(f"[X] Errors: {len(self.errors)}", "red" if self.errors else "green")
        ColorOutput.print_colored(f"⚠️  Warnings: {len(self.warnings)}", "yellow" if self.warnings else "green")
        ColorOutput.print_colored(f"[LOCKED] Security issues: {len(self.security_issues)}", "red" if self.security_issues else "green")
        
        # Print errors
        if self.errors:
            ColorOutput.print_colored(f"\n[X] ERRORS ({len(self.errors)}):", "red", bold=True)
            for error in self.errors:
                ColorOutput.print_colored(error, "red")
        
        # Print security issues
        if self.security_issues:
            ColorOutput.print_colored(f"\n[LOCKED] SECURITY ISSUES ({len(self.security_issues)}):", "red", bold=True)
            for issue in self.security_issues:
                ColorOutput.print_colored(issue, "red")
        
        # Print warnings
        if self.warnings:
            ColorOutput.print_colored(f"\n⚠️  WARNINGS ({len(self.warnings)}):", "yellow", bold=True)
            for warning in self.warnings:
                ColorOutput.print_colored(warning, "yellow")
        
        # Final status
        if not self.errors:
            ColorOutput.print_colored("\n[PARTY] All validations passed! Production environment is ready.", "green", bold=True)
        else:
            ColorOutput.print_colored(f"\n💥 {len(self.errors)} critical issues found. Fix them before deployment!", "red", bold=True)
            
        # Recommendations
        if self.errors or self.security_issues or self.warnings:
            ColorOutput.print_colored(f"\n[BULB] Recommendations:", "cyan", bold=True)
            ColorOutput.print_colored("1. Fix all critical errors before deployment", "cyan")
            ColorOutput.print_colored("2. Review and address security issues", "cyan")
            ColorOutput.print_colored("3. Consider fixing warnings for better configuration", "cyan")
            ColorOutput.print_colored("4. Use strong, unique passwords for all services", "cyan")
            ColorOutput.print_colored("5. Enable all security features in production", "cyan")


def main():
    """Main function"""
    env_file = ".env.production"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        env_file = sys.argv[1]
    
    # Run validation
    validator = EnvironmentValidator(env_file)
    is_valid = validator.validate_all()
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
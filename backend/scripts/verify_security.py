#!/usr/bin/env python3
"""
Security Verification Script
Türkiye Üniversite Sınavları Hazırlık Platformu

Verifies that all security hardening measures are properly configured.
Run this before deploying to production.
"""

import re
import sys
from pathlib import Path
from typing import List


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


class SecurityVerifier:
    """Verifies security configuration"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "backend"
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def verify_all(self) -> bool:
        """Run all verification checks"""
        print_header("Security Verification")
        print_info(f"Project root: {self.project_root}")

        checks = [
            ("Environment Files", self.verify_env_files),
            ("Hardcoded API Keys", self.verify_no_hardcoded_keys),
            ("Git Ignore", self.verify_gitignore),
            ("CORS Configuration", self.verify_cors_config),
            ("Security Modules", self.verify_security_modules),
            ("DDoS Protection", self.verify_ddos_protection),
            ("Requirements", self.verify_requirements),
        ]

        for check_name, check_func in checks:
            print_header(check_name)
            try:
                check_func()
            except Exception as e:
                self.errors.append(f"{check_name}: {str(e)}")
                print_error(f"Check failed: {e}")

        # Print summary
        print_header("Summary")

        if not self.errors and not self.warnings:
            print_success("All security checks passed! ✅")
            return True

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings ({len(self.warnings)}):{Colors.RESET}")
            for warning in self.warnings:
                print_warning(warning)

        if self.errors:
            print(f"\n{Colors.RED}Errors ({len(self.errors)}):{Colors.RESET}")
            for error in self.errors:
                print_error(error)
            return False

        print_warning(f"Checks passed with {len(self.warnings)} warnings")
        return True

    def verify_env_files(self):
        """Verify .env file setup"""
        env_example = self.backend_root / ".env.example"
        env_file = self.backend_root / ".env"

        # Check .env.example exists
        if not env_example.exists():
            self.errors.append(".env.example not found")
            print_error(".env.example not found")
        else:
            print_success(".env.example exists")

            # Check for required keys in .env.example
            required_keys = [
                "OPENAI_API_KEY",
                "HUGGINGFACE_API_KEY",
                "YOUTUBE_API_KEY",
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "DATABASE_URL",
            ]

            with open(env_example, "r", encoding="utf-8") as f:
                content = f.read()
                for key in required_keys:
                    if key in content:
                        print_success(f"{key} defined in .env.example")
                    else:
                        self.warnings.append(f"{key} missing from .env.example")
                        print_warning(f"{key} missing from .env.example")

        # Check .env exists (should NOT be in git)
        if env_file.exists():
            print_info(".env file exists (make sure it's in .gitignore)")
        else:
            self.warnings.append(".env file not found - you'll need to create it")
            print_warning(".env file not found - create from .env.example")

    def verify_no_hardcoded_keys(self):
        """Scan for hardcoded API keys"""
        patterns = [
            (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
            (r"hf_[a-zA-Z0-9]{20,}", "HuggingFace API key"),
            (r"AIza[a-zA-Z0-9_-]{35}", "Google/YouTube API key (real)"),
        ]

        found_issues = False

        # Scan Python files
        for py_file in self.backend_root.rglob("*.py"):
            # Skip this verification script
            if py_file.name == "verify_security.py":
                continue

            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern, key_type in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Ignore test mock keys
                        if "TEST_MOCK" in content or "test-" in match.lower():
                            continue

                        self.errors.append(
                            f"Hardcoded {key_type} found in {py_file.relative_to(self.project_root)}"
                        )
                        print_error(f"Hardcoded {key_type} in {py_file.name}")
                        found_issues = True

        if not found_issues:
            print_success("No hardcoded API keys found")

    def verify_gitignore(self):
        """Verify .gitignore protects .env files"""
        gitignore_paths = [
            self.project_root / ".gitignore",
            self.backend_root / ".gitignore",
        ]

        found_gitignore = False
        for gitignore_path in gitignore_paths:
            if not gitignore_path.exists():
                continue

            found_gitignore = True
            with open(gitignore_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Check for .env protection
                if ".env" in content:
                    print_success(f".env protected in {gitignore_path.name}")
                else:
                    self.errors.append(f".env not in {gitignore_path}")
                    print_error(f".env not protected in {gitignore_path.name}")

                # Check for comprehensive .env patterns
                recommended_patterns = [".env.local", ".env.production", ".env.*"]
                for pattern in recommended_patterns:
                    if pattern in content:
                        print_success(f"{pattern} pattern in .gitignore")
                    else:
                        self.warnings.append(f"{pattern} pattern not in .gitignore")
                        print_warning(f"{pattern} pattern missing from .gitignore")

        if not found_gitignore:
            self.errors.append(".gitignore not found")
            print_error(".gitignore not found")

    def verify_cors_config(self):
        """Verify CORS configuration"""
        config_files = [
            self.backend_root / "config" / "production.yaml",
            self.backend_root / "config" / "development.yaml",
            self.backend_root / "config" / "testing.yaml",
        ]

        for config_file in config_files:
            if not config_file.exists():
                self.warnings.append(f"{config_file.name} not found")
                print_warning(f"{config_file.name} not found")
                continue

            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()

                # Check for wildcard CORS
                if "allow_origins" in content:
                    # Check for wildcard (critical vulnerability)
                    if re.search(r'allow_origins.*["\']\*["\']', content):
                        self.errors.append(f"Wildcard CORS (*) in {config_file.name}")
                        print_error(f"Wildcard CORS found in {config_file.name}")
                    else:
                        print_success(f"No wildcard CORS in {config_file.name}")

                    # Production should not have localhost
                    if config_file.name == "production.yaml" and "localhost" in content:
                        self.warnings.append("Production config contains localhost")
                        print_warning("Production config contains localhost origins")

    def verify_security_modules(self):
        """Verify security modules exist"""
        required_modules = [
            ("core/security_utils.py", "XSS and SQL injection protection"),
            ("core/ddos_protection.py", "DDoS protection"),
            ("core/input_validation.py", "Input validation"),
        ]

        for module_path, description in required_modules:
            full_path = self.backend_root / module_path
            if full_path.exists():
                print_success(f"{module_path} exists ({description})")

                # Check for key classes/functions
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    if "security_utils" in module_path:
                        required_classes = [
                            "XSSProtection",
                            "SQLInjectionProtection",
                            "ComprehensiveInputSanitizer",
                        ]
                        for cls in required_classes:
                            if cls in content:
                                print_success(f"  - {cls} class found")
                            else:
                                self.errors.append(
                                    f"{cls} not found in security_utils.py"
                                )
                                print_error(f"  - {cls} class missing")

                    elif "ddos_protection" in module_path:
                        required_items = [
                            "limiter",
                            "AdaptiveRateLimiter",
                            "IPAccessControl",
                            "setup_ddos_protection",
                        ]
                        for item in required_items:
                            if item in content:
                                print_success(f"  - {item} found")
                            else:
                                self.warnings.append(
                                    f"{item} not found in ddos_protection.py"
                                )
                                print_warning(f"  - {item} missing")

            else:
                self.errors.append(f"{module_path} not found")
                print_error(f"{module_path} not found")

    def verify_ddos_protection(self):
        """Verify DDoS protection setup in main.py"""
        main_py = self.backend_root / "main.py"

        if not main_py.exists():
            self.errors.append("main.py not found")
            print_error("main.py not found")
            return

        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()

            # Check for DDoS protection import and setup
            checks = [
                ("from .core.ddos_protection import", "DDoS module import"),
                ("setup_ddos_protection", "DDoS setup function"),
                ("SlowAPI", "SlowAPI integration"),
            ]

            for check_str, description in checks:
                if check_str in content:
                    print_success(f"{description} found in main.py")
                else:
                    self.warnings.append(f"{description} not found in main.py")
                    print_warning(f"{description} missing from main.py")

    def verify_requirements(self):
        """Verify security dependencies in requirements.txt"""
        requirements_txt = self.backend_root / "requirements.txt"

        if not requirements_txt.exists():
            self.errors.append("requirements.txt not found")
            print_error("requirements.txt not found")
            return

        with open(requirements_txt, "r", encoding="utf-8") as f:
            content = f.read()

            required_packages = [
                ("slowapi", "DDoS protection and rate limiting"),
                ("bleach", "XSS protection"),
                ("pydantic", "Input validation"),
            ]

            for package, description in required_packages:
                if package in content.lower():
                    print_success(f"{package} in requirements.txt ({description})")
                else:
                    self.errors.append(f"{package} missing from requirements.txt")
                    print_error(f"{package} missing from requirements.txt")


def main():
    """Main entry point"""
    # Determine project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    verifier = SecurityVerifier(project_root)
    success = verifier.verify_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

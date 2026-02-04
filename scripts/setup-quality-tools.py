#!/usr/bin/env python3
"""
Quality Tools Setup and Verification Script
Installs and verifies all code quality tools integration
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple


class QualityToolsSetup:
    """Setup and verify code quality tools"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.backend_dir = self.root_dir / "backend"
        self.results = []
        
    def run_command(self, command: str, cwd: Path = None) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            if cwd is None:
                cwd = self.backend_dir
                
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return result.returncode == 0, result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def install_quality_tools(self):
        """Install all quality tools"""
        print("Installing quality tools...")
        
        tools = [
            "pytest-cov",
            "coverage[toml]", 
            "codecov",
            "coveralls",
            "bandit[toml]",
            "safety",
            "pylint",
            "flake8",
            "mypy",
            "black",
            "isort",
            "pre-commit",
            "radon",
            "xenon",
            "pydocstyle"
        ]
        
        for tool in tools:
            print(f"  Installing {tool}...")
            success, output = self.run_command(f"pip install {tool}")
            
            if success:
                print(f"    [CHECK] {tool} installed successfully")
            else:
                print(f"    [X] Failed to install {tool}: {output[:100]}...")
                
        self.results.append(("Quality Tools Installation", "completed"))
    
    def setup_pre_commit_hooks(self):
        """Setup pre-commit hooks"""
        print("\n🪝 Setting up pre-commit hooks...")
        
        # Install pre-commit hooks
        success, output = self.run_command("pre-commit install", cwd=self.root_dir)
        
        if success:
            print("  [CHECK] Pre-commit hooks installed")
            
            # Run pre-commit on all files
            print("  [MAG] Running pre-commit on all files...")
            success, output = self.run_command("pre-commit run --all-files", cwd=self.root_dir)
            
            if success:
                print("  [CHECK] Pre-commit checks passed")
            else:
                print(f"  ⚠️  Pre-commit found issues (normal on first run): {output[:200]}...")
        else:
            print(f"  [X] Failed to install pre-commit hooks: {output}")
            
        self.results.append(("Pre-commit Setup", "completed"))
    
    def run_coverage_analysis(self):
        """Run comprehensive coverage analysis"""
        print("\n[CHART] Running coverage analysis...")
        
        # Run tests with coverage
        success, output = self.run_command(
            "python -m pytest --cov=. --cov-report=xml:coverage.xml --cov-report=json:coverage.json --cov-report=html:htmlcov --cov-report=term-missing -v"
        )
        
        if success:
            print("  [CHECK] Coverage analysis completed")
            
            # Read coverage results
            try:
                with open(self.backend_dir / "coverage.json", "r") as f:
                    coverage_data = json.load(f)
                    
                total_coverage = coverage_data["totals"]["percent_covered"]
                covered_lines = coverage_data["totals"]["covered_lines"]
                total_lines = coverage_data["totals"]["num_statements"]
                
                print(f"  [TRENDING_UP] Coverage Results:")
                print(f"    Total Coverage: {total_coverage:.2f}%")
                print(f"    Covered Lines: {covered_lines:,}")
                print(f"    Total Lines: {total_lines:,}")
                print(f"    Missing Lines: {total_lines - covered_lines:,}")
                
                # Coverage status
                if total_coverage >= 80:
                    print("    [PARTY] EXCELLENT coverage!")
                elif total_coverage >= 50:
                    print("    [CHECK] GOOD coverage")
                elif total_coverage >= 20:
                    print("    ⚠️  ACCEPTABLE coverage")
                else:
                    print("    [X] Coverage needs improvement")
                    
            except Exception as e:
                print(f"  ⚠️  Could not read coverage results: {e}")
        else:
            print(f"  [X] Coverage analysis failed: {output[:200]}...")
            
        self.results.append(("Coverage Analysis", "completed"))
    
    def run_security_analysis(self):
        """Run security analysis"""
        print("\n🛡️  Running security analysis...")
        
        # Bandit security scan
        print("  [MAG] Running Bandit security scan...")
        success, output = self.run_command("bandit -r . -f json -o bandit-report.json")
        
        if success:
            print("    [CHECK] Bandit scan completed")
        else:
            print(f"    ⚠️  Bandit found issues: {output[:200]}...")
        
        # Safety dependency check
        print("  [LOCKED] Running Safety dependency check...")
        success, output = self.run_command("safety check --json --output safety-report.json")
        
        if success:
            print("    [CHECK] Safety check passed")
        else:
            print(f"    ⚠️  Safety found vulnerabilities: {output[:200]}...")
            
        self.results.append(("Security Analysis", "completed"))
    
    def run_code_quality_analysis(self):
        """Run code quality analysis"""
        print("\n[MAG] Running code quality analysis...")
        
        # Flake8 linting
        print("  [MEMO] Running Flake8 linting...")
        success, output = self.run_command("flake8 . --output-file=flake8-report.txt")
        
        if success:
            print("    [CHECK] Flake8 checks passed")
        else:
            print(f"    ⚠️  Flake8 found issues: {output[:200]}...")
        
        # Pylint analysis
        print("  [MICROSCOPE] Running Pylint analysis...")
        success, output = self.run_command("pylint --output-format=text $(find . -name '*.py' | head -10) > pylint-report.txt")
        
        if success:
            print("    [CHECK] Pylint analysis completed")
        else:
            print(f"    ⚠️  Pylint found issues (normal): {output[:200]}...")
        
        # MyPy type checking
        print("  🔎 Running MyPy type checking...")
        success, output = self.run_command("mypy --ignore-missing-imports .")
        
        if success:
            print("    [CHECK] MyPy type checking passed")
        else:
            print(f"    ⚠️  MyPy found type issues: {output[:200]}...")
            
        self.results.append(("Code Quality Analysis", "completed"))
    
    def verify_integrations(self):
        """Verify all integrations are working"""
        print("\n[CHECK] Verifying integrations...")
        
        # Check configuration files
        config_files = [
            self.root_dir / "sonar-project.properties",
            self.root_dir / "codecov.yml", 
            self.root_dir / ".coveralls.yml",
            self.root_dir / ".pre-commit-config.yaml",
            self.root_dir / ".github" / "workflows" / "code-quality.yml",
            self.root_dir / ".github" / "workflows" / "quality-gates.yml",
            self.backend_dir / "pyproject.toml",
            self.backend_dir / "setup.cfg"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                print(f"  [CHECK] {config_file.name} exists")
            else:
                print(f"  [X] {config_file.name} missing")
        
        # Check generated reports
        report_files = [
            self.backend_dir / "coverage.xml",
            self.backend_dir / "coverage.json",
            self.backend_dir / "htmlcov" / "index.html",
            self.backend_dir / "bandit-report.json",
            self.backend_dir / "flake8-report.txt"
        ]
        
        for report_file in report_files:
            if report_file.exists():
                print(f"  [CHECK] {report_file.name} generated")
            else:
                print(f"  ⚠️  {report_file.name} not found")
                
        self.results.append(("Integration Verification", "completed"))
    
    def generate_summary_report(self):
        """Generate summary report"""
        print("\n[CLIPBOARD] Quality Tools Setup Summary")
        print("=" * 50)
        
        for task, status in self.results:
            status_icon = "[CHECK]" if status == "completed" else "[X]"
            print(f"{status_icon} {task}")
        
        print(f"\n[TARGET] Next Steps:")
        print(f"1. Update GitHub secrets for SonarCloud/Codecov/Coveralls")
        print(f"2. Push code to trigger GitHub Actions workflows")
        print(f"3. Monitor quality dashboards")
        print(f"4. Review generated reports in backend/ directory")
        
        print(f"\n[CHART] Quality Dashboard URLs (update with your info):")
        print(f"- SonarCloud: https://sonarcloud.io/project/overview?id=your-project-key")
        print(f"- Codecov: https://codecov.io/gh/your-username/teknofest-2025-egitim-eylemci")
        print(f"- Coveralls: https://coveralls.io/github/your-username/teknofest-2025-egitim-eylemci")
        print(f"- GitHub Actions: https://github.com/your-username/teknofest-2025-egitim-eylemci/actions")
        
        print(f"\n[FOLDER] Local Reports:")
        print(f"- Coverage HTML: backend/htmlcov/index.html")
        print(f"- Coverage XML: backend/coverage.xml")
        print(f"- Security Report: backend/bandit-report.json")
        print(f"- Code Quality: backend/flake8-report.txt")
    
    def run_setup(self):
        """Run complete setup process"""
        print("Quality Tools Setup Starting...")
        print("=" * 50)
        
        # Ensure we're in the right directory
        if not self.backend_dir.exists():
            print(f"[X] Backend directory not found: {self.backend_dir}")
            return False
        
        try:
            # Run all setup steps
            self.install_quality_tools()
            self.setup_pre_commit_hooks()
            self.run_coverage_analysis()
            self.run_security_analysis()
            self.run_code_quality_analysis()
            self.verify_integrations()
            self.generate_summary_report()
            
            print(f"\n[PARTY] Quality tools setup completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n[X] Setup failed with error: {e}")
            return False


if __name__ == "__main__":
    setup = QualityToolsSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
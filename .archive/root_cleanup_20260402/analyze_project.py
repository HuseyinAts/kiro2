#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Project Analysis Tool
Comprehensive analysis of the Turkish University Exam Preparation Platform
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class ProjectAnalyzer:
    """Comprehensive project analysis tool"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / 'backend'
        self.frontend_path = self.project_root / 'frontend'
        self.analysis_data = {}

    def analyze_file_structure(self) -> Dict[str, Any]:
        """Analyze project file structure"""
        structure = {
            'total_files': 0,
            'python_files': 0,
            'typescript_files': 0,
            'test_files': 0,
            'config_files': 0,
            'documentation_files': 0
        }

        file_extensions = {
            '.py': 'python_files',
            '.ts': 'typescript_files',
            '.tsx': 'typescript_files',
            '.js': 'typescript_files',
            '.jsx': 'typescript_files',
            '.yml': 'config_files',
            '.yaml': 'config_files',
            '.json': 'config_files',
            '.md': 'documentation_files',
            '.txt': 'documentation_files'
        }

        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            if any(skip in root for skip in ['node_modules', 'venv', '__pycache__', '.git', 'htmlcov']):
                continue

            for file in files:
                structure['total_files'] += 1

                if file.startswith('test_'):
                    structure['test_files'] += 1

                ext = Path(file).suffix.lower()
                if ext in file_extensions:
                    structure[file_extensions[ext]] += 1

        return structure

    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        deps = {
            'backend': {},
            'frontend': {}
        }

        # Backend dependencies
        requirements_file = self.backend_path / 'requirements.txt'
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
                deps['backend']['total'] = len([l for l in lines if l.strip() and not l.startswith('#')])
                deps['backend']['requirements'] = [l.strip() for l in lines if l.strip() and not l.startswith('#')][:10]

        # Frontend dependencies
        package_json = self.frontend_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)

                deps['frontend']['dependencies'] = len(pkg_data.get('dependencies', {}))
                deps['frontend']['devDependencies'] = len(pkg_data.get('devDependencies', {}))
                deps['frontend']['total'] = deps['frontend']['dependencies'] + deps['frontend']['devDependencies']
            except json.JSONDecodeError:
                deps['frontend']['error'] = 'Invalid package.json'

        return deps

    def analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality metrics"""
        quality = {
            'lines_of_code': 0,
            'complexity_issues': [],
            'duplicate_files': [],
            'large_files': []
        }

        for root, dirs, files in os.walk(self.backend_path):
            if '__pycache__' in root or 'venv' in root:
                continue

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            line_count = len(lines)
                            quality['lines_of_code'] += line_count

                            # Check for large files
                            if line_count > 500:
                                quality['large_files'].append({
                                    'file': filepath,
                                    'lines': line_count
                                })
                    except Exception:
                        continue

        return quality

    def analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage"""
        coverage = {
            'test_files_count': 0,
            'test_directories': [],
            'coverage_data': None
        }

        # Count test files
        for root, dirs, files in os.walk(self.backend_path):
            if '__pycache__' in root:
                continue

            test_files_in_dir = [f for f in files if f.startswith('test_') and f.endswith('.py')]
            if test_files_in_dir:
                coverage['test_files_count'] += len(test_files_in_dir)
                coverage['test_directories'].append({
                    'directory': root,
                    'test_count': len(test_files_in_dir)
                })

        # Try to read coverage data
        coverage_file = self.backend_path / 'coverage.json'
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage['coverage_data'] = json.load(f)
            except Exception:
                coverage['coverage_data'] = 'Error reading coverage.json'

        return coverage

    def analyze_docker_setup(self) -> Dict[str, Any]:
        """Analyze Docker configuration"""
        docker = {
            'dockerfiles': [],
            'docker_compose_files': [],
            'has_docker_setup': False
        }

        # Check for Dockerfiles
        for file in ['Dockerfile', 'Dockerfile.dev', 'Dockerfile.production']:
            if (self.project_root / file).exists():
                docker['dockerfiles'].append(file)
            if (self.backend_path / file).exists():
                docker['dockerfiles'].append(f'backend/{file}')
            if (self.frontend_path / file).exists():
                docker['dockerfiles'].append(f'frontend/{file}')

        # Check for docker-compose files
        for file in ['docker-compose.yml', 'docker-compose.dev.yml', 'docker-compose.production.yml']:
            if (self.project_root / file).exists():
                docker['docker_compose_files'].append(file)

        docker['has_docker_setup'] = bool(docker['dockerfiles'] or docker['docker_compose_files'])

        return docker

    def analyze_security(self) -> Dict[str, Any]:
        """Analyze security aspects"""
        security = {
            'env_files': [],
            'secret_keys_found': False,
            'security_files': []
        }

        # Check for environment files
        env_patterns = ['.env', '.env.example', '.env.local', '.env.production']
        for pattern in env_patterns:
            if (self.project_root / pattern).exists():
                security['env_files'].append(pattern)

        # Check for security-related files
        security_files = ['nginx.conf', 'ssl', 'secrets.yaml', '.gitignore']
        for sec_file in security_files:
            if (self.project_root / sec_file).exists():
                security['security_files'].append(sec_file)

        return security

    def run_analysis(self) -> Dict[str, Any]:
        """Run complete project analysis"""
        print("[SCAN] Starting comprehensive project analysis...")

        self.analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'project_info': {
                'name': 'KIRO2',
                'description': 'Turkish University Exam Preparation Platform',
                'type': 'Full-stack web application'
            },
            'file_structure': self.analyze_file_structure(),
            'dependencies': self.analyze_dependencies(),
            'code_quality': self.analyze_code_quality(),
            'test_coverage': self.analyze_test_coverage(),
            'docker_setup': self.analyze_docker_setup(),
            'security': self.analyze_security()
        }

        return self.analysis_data

    def generate_report(self) -> str:
        """Generate analysis report"""
        if not self.analysis_data:
            self.run_analysis()

        report = []
        report.append("=" * 70)
        report.append("KIRO2 PROJECT ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {self.analysis_data['timestamp']}")
        report.append("")

        # File Structure
        fs = self.analysis_data['file_structure']
        report.append("[INFO] FILE STRUCTURE")
        report.append("-" * 30)
        report.append(f"Total Files: {fs['total_files']}")
        report.append(f"Python Files: {fs['python_files']}")
        report.append(f"TypeScript/JS Files: {fs['typescript_files']}")
        report.append(f"Test Files: {fs['test_files']}")
        report.append(f"Config Files: {fs['config_files']}")
        report.append(f"Documentation Files: {fs['documentation_files']}")
        report.append("")

        # Dependencies
        deps = self.analysis_data['dependencies']
        report.append("[INFO] DEPENDENCIES")
        report.append("-" * 30)
        report.append(f"Backend Dependencies: {deps['backend'].get('total', 0)}")
        if 'frontend' in deps and 'total' in deps['frontend']:
            report.append(f"Frontend Dependencies: {deps['frontend']['total']}")
        report.append("")

        # Code Quality
        quality = self.analysis_data['code_quality']
        report.append("[INFO] CODE QUALITY")
        report.append("-" * 30)
        report.append(f"Total Lines of Code: {quality['lines_of_code']}")
        report.append(f"Large Files (>500 lines): {len(quality['large_files'])}")
        report.append("")

        # Test Coverage
        tests = self.analysis_data['test_coverage']
        report.append("[INFO] TEST COVERAGE")
        report.append("-" * 30)
        report.append(f"Test Files: {tests['test_files_count']}")
        report.append(f"Test Directories: {len(tests['test_directories'])}")
        report.append("")

        # Docker Setup
        docker = self.analysis_data['docker_setup']
        report.append("[INFO] DOCKER SETUP")
        report.append("-" * 30)
        report.append(f"Has Docker Setup: {docker['has_docker_setup']}")
        report.append(f"Dockerfiles: {len(docker['dockerfiles'])}")
        report.append(f"Docker Compose Files: {len(docker['docker_compose_files'])}")
        report.append("")

        # Security
        security = self.analysis_data['security']
        report.append("[INFO] SECURITY")
        report.append("-" * 30)
        report.append(f"Environment Files: {len(security['env_files'])}")
        report.append(f"Security Files: {len(security['security_files'])}")
        report.append("")

        # Recommendations
        report.append("[RECOMMEND] RECOMMENDATIONS")
        report.append("-" * 30)

        if fs['test_files'] < fs['python_files'] * 0.5:
            report.append("- Increase test coverage (consider adding more test files)")

        if quality['lines_of_code'] > 50000:
            report.append("- Consider code refactoring for better maintainability")

        if not docker['has_docker_setup']:
            report.append("- Add Docker configuration for easier deployment")

        if len(security['env_files']) == 0:
            report.append("- Add environment configuration files")

        report.append("")
        report.append("=" * 70)
        report.append("END OF REPORT")
        report.append("=" * 70)

        return "\n".join(report)

    def save_report(self, filename: str = None) -> str:
        """Save analysis report to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'project_analysis_{timestamp}.txt'

        report_content = self.generate_report()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # Also save JSON data
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_data, f, indent=2, default=str)

        return filename

def main():
    """Main function"""
    analyzer = ProjectAnalyzer()

    # Run analysis
    print("[START] Initializing project analysis...")
    analyzer.run_analysis()

    # Generate and display report
    report = analyzer.generate_report()
    print(report)

    # Save report
    report_file = analyzer.save_report()
    print(f"\n[OK] Analysis completed! Report saved to: {report_file}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Master Dashboard
Interactive management interface for the entire KIRO2 platform
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any

class Colors:
    """Terminal colors for better UI"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class KiroMasterDashboard:
    """Master dashboard for KIRO2 platform management"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.backend_path = os.path.join(self.project_root, 'backend')
        self.frontend_path = os.path.join(self.project_root, 'frontend')
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        """Print dashboard header"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 70)
        print("[TARGET] KIRO2 MASTER DASHBOARD")
        print("Turkish University Exam Preparation Platform")
        print("=" * 70)
        print(f"{Colors.ENDC}")
        print(f"{Colors.OKCYAN}[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print()
        
    def run_command(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Run shell command and return result"""
        try:
            if cwd is None:
                cwd = self.project_root
                
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd,
                capture_output=True, 
                text=True,
                encoding='utf-8'
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def check_system_status(self) -> Dict[str, bool]:
        """Check system components status"""
        status = {}
        
        print(f"{Colors.OKBLUE}[SCAN] System Status Check...{Colors.ENDC}")
        
        # Check Python
        python_check = self.run_command('python --version')
        status['python'] = python_check['success']
        
        # Check Node.js
        node_check = self.run_command('node --version')
        status['nodejs'] = node_check['success']
        
        # Check Docker
        docker_check = self.run_command('docker --version')
        status['docker'] = docker_check['success']
        
        # Check Backend files
        status['backend'] = os.path.exists(self.backend_path)
        
        # Check Frontend files  
        status['frontend'] = os.path.exists(self.frontend_path)
        
        # Check requirements
        req_file = os.path.join(self.backend_path, 'requirements.txt')
        status['requirements'] = os.path.exists(req_file)
        
        return status
    
    def display_status(self, status: Dict[str, bool]):
        """Display system status"""
        print(f"{Colors.OKGREEN}[OK] System Status:{Colors.ENDC}")
        
        for component, is_ok in status.items():
            icon = "[OK]" if is_ok else "[ERROR]"
            color = Colors.OKGREEN if is_ok else Colors.FAIL
            print(f"  {icon} {color}{component.capitalize()}: {'OK' if is_ok else 'NOT FOUND'}{Colors.ENDC}")
        print()
        
    def show_main_menu(self):
        """Display main menu options"""
        print(f"{Colors.BOLD}[MENU] MAIN MENU:{Colors.ENDC}")
        print("1. [SCAN] Project Analysis & Health Check")
        print("2. [TEST] Test Coverage Analysis")
        print("3. [START] Build & Deploy")
        print("4. [STATS] Performance Monitoring")
        print("5. [DOCKER] Docker Management")
        print("6. [FIX] Quick Fixes & Optimization")
        print("7. [BOOST] Test Coverage Boost")
        print("8. [SECURE] Security & Deployment Fix")
        print("9. [PKG] Dependency Management")
        print("10. [REPORT] Generate Reports")
        print("11. [DEV] Live Development Server")
        print("0. [ERROR] Exit")
        print()
        
    def project_analysis(self):
        """Run comprehensive project analysis"""
        print(f"{Colors.OKBLUE}[SCAN] Running Project Analysis...{Colors.ENDC}")
        
        # Run analyze_project.py
        result = self.run_command('python analyze_project.py')
        
        if result['success']:
            print(f"{Colors.OKGREEN}[OK] Analysis completed successfully!{Colors.ENDC}")
            if result['stdout']:
                print(result['stdout'])
        else:
            print(f"{Colors.FAIL}[ERROR] Analysis failed:{Colors.ENDC}")
            print(result['stderr'])
            
    def test_coverage_analysis(self):
        """Run test coverage analysis"""
        print(f"{Colors.OKBLUE}[TEST] Running Test Coverage Analysis...{Colors.ENDC}")
        
        os.chdir(self.backend_path)
        
        # Run pytest with coverage
        result = self.run_command('pytest --cov=. --cov-report=html --cov-report=term', self.backend_path)
        
        if result['success']:
            print(f"{Colors.OKGREEN}[OK] Test coverage completed!{Colors.ENDC}")
            print("[STATS] Coverage report generated in htmlcov/")
        else:
            print(f"{Colors.WARNING}[WARN] Test coverage issues:{Colors.ENDC}")
            print(result['stderr'])
            
    def docker_build_and_test(self):
        """Build and test with Docker"""
        print(f"{Colors.OKBLUE}[DOCKER] Docker Build & Test...{Colors.ENDC}")
        
        # Docker build
        print("[BUILD] Building Docker containers...")
        build_result = self.run_command('docker-compose build --no-cache')
        
        if build_result['success']:
            print(f"{Colors.OKGREEN}[OK] Docker build successful!{Colors.ENDC}")
            
            # Docker up
            print("[START] Starting containers...")
            up_result = self.run_command('docker-compose up -d')
            
            if up_result['success']:
                print(f"{Colors.OKGREEN}[OK] Containers started successfully!{Colors.ENDC}")
                print("[WEB] Access the application at: http://localhost:8000")
            else:
                print(f"{Colors.FAIL}[ERROR] Failed to start containers:{Colors.ENDC}")
                print(up_result['stderr'])
        else:
            print(f"{Colors.FAIL}[ERROR] Docker build failed:{Colors.ENDC}")
            print(build_result['stderr'])
            
    def boost_test_coverage(self):
        """Boost test coverage"""
        print(f"{Colors.OKBLUE}[BOOST] Boosting Test Coverage...{Colors.ENDC}")
        
        result = self.run_command('python boost_test_coverage.py')
        
        if result['success']:
            print(f"{Colors.OKGREEN}[OK] Coverage boost completed!{Colors.ENDC}")
            print(result['stdout'])
        else:
            print(f"{Colors.FAIL}[ERROR] Coverage boost failed:{Colors.ENDC}")
            print(result['stderr'])
            
    def quick_fix_generator(self):
        """Run quick fix generator"""
        print(f"{Colors.OKBLUE}[FIX] Running Quick Fix Generator...{Colors.ENDC}")
        
        result = self.run_command('python quick_fix_generator.py')
        
        if result['success']:
            print(f"{Colors.OKGREEN}[OK] Quick fixes completed!{Colors.ENDC}")
            print(result['stdout'])
        else:
            print(f"{Colors.FAIL}[ERROR] Quick fixes failed:{Colors.ENDC}")
            print(result['stderr'])
            
    def development_server(self):
        """Start development servers"""
        print(f"{Colors.OKBLUE}[DEV] Starting Development Servers...{Colors.ENDC}")
        
        print("[START] Starting Backend (FastAPI)...")
        backend_cmd = 'uvicorn main:app --reload --host 0.0.0.0 --port 8000'
        
        print("[UI] Starting Frontend (Vite)...")
        frontend_cmd = 'npm run dev'
        
        print(f"{Colors.WARNING}[WARN] Run these commands in separate terminals:{Colors.ENDC}")
        print(f"Backend: cd backend && {backend_cmd}")
        print(f"Frontend: cd frontend && {frontend_cmd}")
        
    def dependency_management(self):
        """Manage project dependencies"""
        print(f"{Colors.OKBLUE}[PKG] Dependency Management...{Colors.ENDC}")
        
        print("1. Install Backend Dependencies")
        print("2. Install Frontend Dependencies") 
        print("3. Check for Updates")
        print("4. Security Audit")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == '1':
            result = self.run_command('pip install -r requirements.txt', self.backend_path)
            print("[OK] Backend dependencies installed" if result['success'] else "[ERROR] Failed")
        elif choice == '2':
            result = self.run_command('npm install', self.frontend_path)
            print("[OK] Frontend dependencies installed" if result['success'] else "[ERROR] Failed")
        elif choice == '3':
            print("[SCAN] Checking for updates...")
            pip_result = self.run_command('pip list --outdated', self.backend_path)
            npm_result = self.run_command('npm outdated', self.frontend_path)
        elif choice == '4':
            print("[SECURE] Running security audit...")
            pip_audit = self.run_command('pip audit', self.backend_path)
            npm_audit = self.run_command('npm audit', self.frontend_path)
            
    def generate_reports(self):
        """Generate various reports"""
        print(f"{Colors.OKBLUE}[REPORT] Generating Reports...{Colors.ENDC}")
        
        reports = {
            'project_structure': self.run_command('find . -type f -name "*.py" | head -20'),
            'test_files': self.run_command('find . -name "test_*.py" | wc -l'),
            'code_quality': self.run_command('find . -name "*.py" -exec wc -l {} + | tail -1')
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'dashboard_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(reports, f, indent=2)
            
        print(f"[MENU] Report generated: {report_file}")
        
    def run(self):
        """Main dashboard loop"""
        while True:
            self.clear_screen()
            self.print_header()
            
            # Check system status
            status = self.check_system_status()
            self.display_status(status)
            
            # Show menu
            self.show_main_menu()
            
            try:
                choice = input(f"{Colors.BOLD}Select option (0-11): {Colors.ENDC}").strip()
                
                if choice == '0':
                    print(f"{Colors.OKGREEN}[BYE] Goodbye!{Colors.ENDC}")
                    break
                elif choice == '1':
                    self.project_analysis()
                elif choice == '2':
                    self.test_coverage_analysis()
                elif choice == '3':
                    self.docker_build_and_test()
                elif choice == '4':
                    print("[STATS] Performance monitoring integration coming soon...")
                elif choice == '5':
                    self.docker_build_and_test()
                elif choice == '6':
                    self.quick_fix_generator()
                elif choice == '7':
                    self.boost_test_coverage()
                elif choice == '8':
                    self.quick_fix_generator()
                elif choice == '9':
                    self.dependency_management()
                elif choice == '10':
                    self.generate_reports()
                elif choice == '11':
                    self.development_server()
                else:
                    print(f"{Colors.WARNING}[WARN] Invalid option. Please try again.{Colors.ENDC}")
                    
                input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")
                
            except KeyboardInterrupt:
                print(f"\n{Colors.OKGREEN}[BYE] Goodbye!{Colors.ENDC}")
                break
            except Exception as e:
                print(f"{Colors.FAIL}[ERROR] Error: {e}{Colors.ENDC}")
                input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")

if __name__ == "__main__":
    dashboard = KiroMasterDashboard()
    dashboard.run()
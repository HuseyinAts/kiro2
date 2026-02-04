#!/usr/bin/env python3
"""
Branch Protection Setup Script
Configures GitHub branch protection rules to enforce our CI/CD quality gates.
"""

import os
import requests
import json
from typing import Dict, Any

class BranchProtectionSetup:
    """GitHub branch protection configuration manager"""
    
    def __init__(self, repo_owner: str, repo_name: str, token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def get_protection_config(self, branch_name: str) -> Dict[str, Any]:
        """Get branch protection configuration"""
        
        # Required status checks based on our CI/CD workflows
        required_checks = [
            "Modern Code Quality",
            "Fast Comprehensive Tests (config)",
            "Fast Comprehensive Tests (base-service)", 
            "Fast Comprehensive Tests (exceptions)",
            "Fast Comprehensive Tests (database)",
            "Fast Comprehensive Tests (logger)",
            "Coverage Analysis",
            "Security & Dependencies",
            "Modern Quality Gate"
        ]
        
        # Enhanced protection for main/master branches
        if branch_name in ["main", "master"]:
            required_checks.extend([
                "Performance Check",
                "Code Quality Analysis / Test and Coverage",
                "Code Quality Analysis / SonarCloud Analysis"
            ])
        
        config = {
            "required_status_checks": {
                "strict": True,  # Require branches to be up to date
                "contexts": required_checks
            },
            "enforce_admins": False,  # Allow admins to bypass in emergencies
            "required_pull_request_reviews": {
                "required_approving_review_count": 1 if branch_name == "develop" else 2,
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": True,
                "require_last_push_approval": False
            },
            "restrictions": None,  # No user/team restrictions
            "allow_force_pushes": False,
            "allow_deletions": False,
            "block_creations": False,
            "required_conversation_resolution": True
        }
        
        return config
    
    def setup_branch_protection(self, branch_name: str) -> bool:
        """Setup branch protection for specified branch"""
        
        print(f"🔒 Setting up branch protection for '{branch_name}'...")
        
        config = self.get_protection_config(branch_name)
        
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/branches/{branch_name}/protection"
        
        try:
            response = requests.put(url, headers=self.headers, json=config)
            
            if response.status_code == 200:
                print(f"✅ Branch protection updated for '{branch_name}'")
                return True
            elif response.status_code == 403:
                print(f"❌ Permission denied. Make sure the token has admin access to the repository.")
                return False
            else:
                print(f"❌ Failed to setup protection for '{branch_name}': {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up branch protection: {e}")
            return False
    
    def create_rulesets(self) -> bool:
        """Create modern repository rulesets (newer GitHub feature)"""
        
        print("🚀 Creating modern repository rulesets...")
        
        # Modern ruleset configuration
        ruleset_config = {
            "name": "Modern CI/CD Quality Gates",
            "target": "branch",
            "enforcement": "active",
            "conditions": {
                "ref_name": {
                    "include": ["refs/heads/main", "refs/heads/master", "refs/heads/develop"],
                    "exclude": []
                }
            },
            "rules": [
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [
                            {
                                "context": "Modern Code Quality",
                                "integration_id": None
                            },
                            {
                                "context": "Coverage Analysis", 
                                "integration_id": None
                            },
                            {
                                "context": "Security & Dependencies",
                                "integration_id": None
                            },
                            {
                                "context": "Modern Quality Gate",
                                "integration_id": None
                            }
                        ]
                    }
                },
                {
                    "type": "pull_request",
                    "parameters": {
                        "required_approving_review_count": 1,
                        "dismiss_stale_reviews_on_push": True,
                        "require_code_owner_review": True,
                        "require_last_push_approval": False
                    }
                },
                {
                    "type": "required_conversation_resolution"
                }
            ]
        }
        
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/rulesets"
        
        try:
            response = requests.post(url, headers=self.headers, json=ruleset_config)
            
            if response.status_code == 201:
                print("✅ Modern ruleset created successfully")
                return True
            else:
                print(f"❌ Failed to create ruleset: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating ruleset: {e}")
            return False
    
    def setup_all_protections(self) -> bool:
        """Setup protection for all important branches"""
        
        print("🛡️ Setting up comprehensive branch protection...")
        print("=" * 60)
        
        branches_to_protect = ["main", "master", "develop"]
        success_count = 0
        
        for branch in branches_to_protect:
            if self.setup_branch_protection(branch):
                success_count += 1
        
        # Try to create modern rulesets
        if self.create_rulesets():
            print("✅ Modern rulesets created")
        
        print("=" * 60)
        print(f"📊 Summary: {success_count}/{len(branches_to_protect)} branches protected")
        
        if success_count == len(branches_to_protect):
            print("🎉 All branch protections configured successfully!")
            return True
        else:
            print("⚠️ Some branch protections failed to configure")
            return False
    
    def verify_protection(self, branch_name: str) -> bool:
        """Verify branch protection is working"""
        
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/branches/{branch_name}/protection"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                protection = response.json()
                print(f"✅ Branch '{branch_name}' is protected")
                
                # Check key protections
                required_checks = protection.get('required_status_checks', {})
                pr_reviews = protection.get('required_pull_request_reviews', {})
                
                print(f"  - Required status checks: {len(required_checks.get('contexts', []))}")
                print(f"  - Required reviews: {pr_reviews.get('required_approving_review_count', 0)}")
                
                return True
            else:
                print(f"❌ Branch '{branch_name}' is not protected")
                return False
                
        except Exception as e:
            print(f"❌ Error checking protection for '{branch_name}': {e}")
            return False


def main():
    """Main execution function"""
    
    print("🚀 GitHub Branch Protection Setup")
    print("=" * 50)
    
    # Get configuration from environment or prompt
    repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER") or input("Repository owner: ")
    repo_name = os.getenv("GITHUB_REPOSITORY_NAME") or input("Repository name: ")
    token = os.getenv("GITHUB_TOKEN") or input("GitHub token (with admin access): ")
    
    if not all([repo_owner, repo_name, token]):
        print("❌ Missing required configuration")
        return False
    
    # Setup branch protection
    bp_setup = BranchProtectionSetup(repo_owner, repo_name, token)
    
    if bp_setup.setup_all_protections():
        print("\n🎯 Recommended next steps:")
        print("1. Test the CI/CD pipeline with a test PR")
        print("2. Verify all status checks are working")
        print("3. Train team on new quality gates")
        print("4. Monitor build times and adjust as needed")
        
        return True
    else:
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
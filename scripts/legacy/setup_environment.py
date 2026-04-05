#!/usr/bin/env python3
"""
Environment Setup Script
Türkiye Üniversite Sınavları Hazırlık Platformu
"""
import os
import sys
import shutil
from pathlib import Path


def setup_environment(env_type="development"):
    """
    Setup environment configuration based on type
    
    Args:
        env_type (str): Environment type (development, production, docker)
    """
    
    print(f"[ROCKET] Setting up {env_type} environment...")
    
    # Environment file mapping
    env_files = {
        "development": ".env.development",
        "production": ".env.production",
        "docker": ".env.docker"
    }
    
    if env_type not in env_files:
        print(f"[X] Invalid environment type: {env_type}")
        print(f"Available types: {', '.join(env_files.keys())}")
        return False
    
    source_file = env_files[env_type]
    target_file = ".env"
    
    # Check if source environment file exists
    if not os.path.exists(source_file):
        print(f"[X] Environment file not found: {source_file}")
        return False
    
    # Copy environment file
    try:
        shutil.copy2(source_file, target_file)
        print(f"[CHECK] Copied {source_file} to {target_file}")
    except Exception as e:
        print(f"[X] Error copying environment file: {e}")
        return False
    
    # Set up directories
    directories = [
        "logs",
        "cache",
        "uploads",
        "temp",
        "backups"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[CHECK] Created directory: {directory}")
    
    # Environment-specific setup
    if env_type == "development":
        setup_development()
    elif env_type == "production":
        setup_production()
    elif env_type == "docker":
        setup_docker()
    
    print(f"[PARTY] {env_type.title()} environment setup completed!")
    return True


def setup_development():
    """Setup development-specific configurations"""
    print("[TOOL] Setting up development environment...")
    
    # Create development-specific directories
    dev_dirs = [
        "backend/logs",
        "backend/cache",
        "frontend/dist",
        "test_data"
    ]
    
    for directory in dev_dirs:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[CHECK] Created dev directory: {directory}")


def setup_production():
    """Setup production-specific configurations"""
    print("[TOOL] Setting up production environment...")
    
    # Validate critical environment variables
    critical_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL"
    ]
    
    print("⚠️ IMPORTANT: Please ensure the following environment variables are properly configured:")
    for var in critical_vars:
        print(f"  - {var}")
    
    # Create production-specific directories
    prod_dirs = [
        "logs/production",
        "backups/database",
        "ssl",
        "uploads/secure"
    ]
    
    for directory in prod_dirs:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[CHECK] Created prod directory: {directory}")


def setup_docker():
    """Setup Docker-specific configurations"""
    print("[TOOL] Setting up Docker environment...")
    
    # Check if Docker is available
    if shutil.which("docker") is None:
        print("⚠️ Docker not found. Please install Docker to use this environment.")
    else:
        print("[CHECK] Docker found")
    
    # Create Docker-specific directories
    docker_dirs = [
        "docker/logs",
        "docker/data",
        "docker/config"
    ]
    
    for directory in docker_dirs:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[CHECK] Created docker directory: {directory}")


def validate_environment():
    """Validate current environment setup"""
    print("[MAG] Validating environment setup...")
    
    required_files = [
        ".env",
        "backend/requirements.txt",
        "frontend/package.json"
    ]
    
    all_valid = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[CHECK] Found: {file_path}")
        else:
            print(f"[X] Missing: {file_path}")
            all_valid = False
    
    if all_valid:
        print("[PARTY] Environment validation successful!")
    else:
        print("[X] Environment validation failed!")
    
    return all_valid


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python setup_environment.py <environment_type>")
        print("Environment types: development, production, docker")
        sys.exit(1)
    
    env_type = sys.argv[1].lower()
    
    if setup_environment(env_type):
        validate_environment()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
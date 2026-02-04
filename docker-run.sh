#!/bin/bash

# Docker Run Helper Script

echo "Teknofest 2025 - Education Platform Docker Setup"
echo "================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys."
    echo ""
fi

# Menu
echo "Select an option:"
echo "1) Run minimal setup (optimized for current implementation)"
echo "2) Run development setup (with hot reload)"
echo "3) Run full setup (with all services)"
echo "4) Stop all containers"
echo "5) Clean up (remove containers and volumes)"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "Starting minimal setup..."
        docker-compose -f docker-compose.minimal.yml up --build
        ;;
    2)
        echo "Starting development setup with hot reload..."
        docker-compose -f docker-compose.dev.yml up
        ;;
    3)
        echo "Starting full setup..."
        docker-compose up --build
        ;;
    4)
        echo "Stopping containers..."
        docker-compose -f docker-compose.minimal.yml down
        docker-compose -f docker-compose.dev.yml down
        docker-compose down
        ;;
    5)
        echo "Cleaning up..."
        docker-compose -f docker-compose.minimal.yml down -v
        docker-compose -f docker-compose.dev.yml down -v
        docker-compose down -v
        echo "✅ All containers and volumes removed"
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac
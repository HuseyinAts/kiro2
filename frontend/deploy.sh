#!/bin/bash

# Frontend Production Deployment Script

set -e

echo "🚀 Starting Frontend Production Deployment..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ .env.production file not found. Please create it first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm ci --only=production

# Build for production
echo "🔨 Building for production..."
npm run build:prod

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Build failed. dist directory not found."
    exit 1
fi

# Optimize static assets
echo "🎨 Build completed successfully!"
echo "📁 Production files are in the 'dist' directory"

# Optional: Deploy to server
if [ "$1" == "--deploy" ]; then
    echo "🌐 Deploying to production server..."
    # Add your deployment commands here
    # Example: rsync -avz dist/ user@server:/var/www/html/
fi

echo "✅ Frontend production build completed!"
echo "📊 Build statistics:"
du -sh dist/
echo ""
echo "🎯 Next steps:"
echo "  1. Review the build output in 'dist' directory"
echo "  2. Test the production build: npm run preview"
echo "  3. Deploy to your production server"
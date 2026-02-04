@echo off

REM Frontend Production Deployment Script for Windows

echo Starting Frontend Production Deployment...

REM Check if .env.production exists
if not exist .env.production (
    echo .env.production file not found. Please create it first.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
call npm ci --only=production

REM Build for production
echo Building for production...
call npm run build:prod

REM Check if build was successful
if not exist dist (
    echo Build failed. dist directory not found.
    exit /b 1
)

echo Build completed successfully!
echo Production files are in the 'dist' directory

REM Optional: Deploy to server
if "%1"=="--deploy" (
    echo Deploying to production server...
    REM Add your deployment commands here
)

echo Frontend production build completed!
echo.
echo Next steps:
echo   1. Review the build output in 'dist' directory
echo   2. Test the production build: npm run preview
echo   3. Deploy to your production server
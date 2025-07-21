# Airflow Setup Script for Windows (PowerShell)
# This script sets up Apache Airflow with Docker

Write-Host "Setting up Apache Airflow with Docker..." -ForegroundColor Green

# Set AIRFLOW_UID environment variable
$env:AIRFLOW_UID = "50000"
Write-Host "Set AIRFLOW_UID to 50000" -ForegroundColor Yellow

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\plugins" | Out-Null
New-Item -ItemType Directory -Force -Path ".\config" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data" | Out-Null

# Clean up any existing containers
Write-Host "Cleaning up existing containers..." -ForegroundColor Yellow
docker-compose down -v 2>$null

# Pull the latest Airflow image
Write-Host "Pulling Airflow Docker image..." -ForegroundColor Yellow
docker pull apache/airflow:3.0.3-python3.11

# Initialize Airflow database
Write-Host "Initializing Airflow database..." -ForegroundColor Yellow
docker-compose up airflow-init

if ($LASTEXITCODE -eq 0) {
    Write-Host "Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start Airflow:" -ForegroundColor Cyan
    Write-Host "  docker-compose up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "To access Airflow Web UI:" -ForegroundColor Cyan
    Write-Host "  Open http://localhost:8080" -ForegroundColor White
    Write-Host "  Username: airflow" -ForegroundColor White
    Write-Host "  Password: airflow" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop Airflow:" -ForegroundColor Cyan
    Write-Host "  docker-compose down" -ForegroundColor White
}
else {
    Write-Host "Setup failed! Please check the error messages above." -ForegroundColor Red
}

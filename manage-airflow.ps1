# REDataPipe Airflow Management Script for Windows PowerShell

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("start", "stop", "restart", "logs", "web", "status", "dag-list", "dag-test", "cleanup", "help")]
    [string]$Command
)

function Show-Usage {
    Write-Host ""
    Write-Host "REDataPipe Airflow Management Script" -ForegroundColor Green
    Write-Host "Usage: .\manage-airflow.ps1 [COMMAND]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  start       Start Airflow services"
    Write-Host "  stop        Stop Airflow services"
    Write-Host "  restart     Restart Airflow services"
    Write-Host "  logs        Show logs for all services"
    Write-Host "  web         Open Airflow web UI"
    Write-Host "  status      Show status of all services"
    Write-Host "  dag-list    List all DAGs"
    Write-Host "  dag-test    Test the coin sentiment DAG"
    Write-Host "  cleanup     Remove all containers and volumes"
    Write-Host "  help        Show this help message"
    Write-Host ""
}

switch ($Command) {
    "start" {
        Write-Host "Starting Airflow services..." -ForegroundColor Green
        docker-compose up -d
        Write-Host "Services started. Access the web UI at http://localhost:8080" -ForegroundColor Green
        Write-Host "Username: airflow, Password: airflow" -ForegroundColor Yellow
    }
    "stop" {
        Write-Host "Stopping Airflow services..." -ForegroundColor Yellow
        docker-compose down
    }
    "restart" {
        Write-Host "Restarting Airflow services..." -ForegroundColor Yellow
        docker-compose down
        docker-compose up -d
        Write-Host "Services restarted." -ForegroundColor Green
    }
    "logs" {
        Write-Host "Showing logs for all services..." -ForegroundColor Cyan
        docker-compose logs -f
    }
    "web" {
        Write-Host "Opening Airflow web UI..." -ForegroundColor Green
        Start-Process "http://localhost:8080"
    }
    "status" {
        Write-Host "Checking service status..." -ForegroundColor Cyan
        docker-compose ps
    }
    "dag-list" {
        Write-Host "Listing all DAGs..." -ForegroundColor Cyan
        docker-compose exec airflow-scheduler airflow dags list
    }
    "dag-test" {
        Write-Host "Testing coin_news_sentiment_pipeline DAG..." -ForegroundColor Cyan
        docker-compose exec airflow-scheduler airflow dags test coin_news_sentiment_pipeline 2024-01-01
    }
    "cleanup" {
        Write-Host "Cleaning up containers and volumes..." -ForegroundColor Red
        $confirm = Read-Host "Are you sure you want to remove all containers and volumes? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            docker-compose down -v
            docker system prune -f
            Write-Host "Cleanup completed." -ForegroundColor Green
        }
        else {
            Write-Host "Cleanup cancelled." -ForegroundColor Yellow
        }
    }
    "help" {
        Show-Usage
    }
}

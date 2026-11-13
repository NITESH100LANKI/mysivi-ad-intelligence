<#
.SYNOPSIS
    MySivi Ad Intelligence & Creative Analysis System - Windows Control Script
.DESCRIPTION
    Automates environment verification, pipeline execution, test running, and local service management.
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("run-pipeline", "test", "start-report-service", "start-docker", "stop-docker", "status")]
    [string]$Action = "run-pipeline",

    [Parameter()]
    [ValidateSet("mock", "live")]
    [string]$Mode = "mock"
)

$PythonExe = "C:\Users\psc\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   MySivi Ad Intelligence & Creative Analysis System - Control Center    " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Check .env
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env not found. Initializing from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[✓] Created .env from template. Configure API keys if running live." -ForegroundColor Green
}

switch ($Action) {
    "run-pipeline" {
        Write-Host "[*] Executing Ad Intelligence Pipeline in mode: $Mode..." -ForegroundColor Yellow
        & $PythonExe run_pipeline.py --mode $Mode
        Write-Host "`n[✓] Pipeline execution finished!" -ForegroundColor Green
        Write-Host "Deliverable 1 (PDF): reports\MySivi_Ad_Intelligence_Report.pdf" -ForegroundColor Cyan
        Write-Host "Deliverable 2 (Workflow JSON): n8n\mysivi_ad_intelligence_workflow.json" -ForegroundColor Cyan
        Write-Host "Deliverable 3 (Loom Script): docs\LOOM_DEMO_SCRIPT.md" -ForegroundColor Cyan
    }

    "test" {
        Write-Host "[*] Running automated test suite with pytest..." -ForegroundColor Yellow
        & $PythonExe -m pytest -v tests/
    }

    "start-report-service" {
        Write-Host "[*] Starting PDF Report Generation HTTP Service on port 5000..." -ForegroundColor Yellow
        Write-Host "Endpoints available: http://localhost:5000/health, POST /generate-report" -ForegroundColor Gray
        & $PythonExe -m backend.report.report_service 5000
    }

    "start-docker" {
        Write-Host "[*] Starting n8n and Report Service via Docker Compose..." -ForegroundColor Yellow
        docker compose up -d
        Write-Host "[✓] Services started. Open http://localhost:5678 to access n8n." -ForegroundColor Green
    }

    "stop-docker" {
        Write-Host "[*] Stopping Docker Compose services..." -ForegroundColor Yellow
        docker compose down
        Write-Host "[✓] Docker services stopped." -ForegroundColor Green
    }

    "status" {
        Write-Host "Project Status:" -ForegroundColor Yellow
        $pdf = Get-Item "reports\MySivi_Ad_Intelligence_Report.pdf" -ErrorAction SilentlyContinue
        $wf = Get-Item "n8n\mysivi_ad_intelligence_workflow.json" -ErrorAction SilentlyContinue
        $loom = Get-Item "docs\LOOM_DEMO_SCRIPT.md" -ErrorAction SilentlyContinue

        Write-Host " - PDF Report: $(if ($pdf) {"Present ($($pdf.Length) bytes)"} else {"Missing"})"
        Write-Host " - Workflow JSON: $(if ($wf) {"Present ($($wf.Length) bytes)"} else {"Missing"})"
        Write-Host " - Loom Script: $(if ($loom) {"Present ($($loom.Length) bytes)"} else {"Missing"})"
    }
}


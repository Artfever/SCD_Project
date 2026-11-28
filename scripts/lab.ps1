<#
  Start only what the current task needs, to stay inside 24 GB (docs/resource-budget.md).
  Usage: .\scripts\lab.ps1 dev | cluster | stop | status
#>
param([Parameter(Mandatory)][ValidateSet('dev', 'cluster', 'stop', 'status')][string]$Mode)

$ErrorActionPreference = 'Stop'
$Profile_ = 'scd-project'
$NodeMemoryMb = 7168
$Root = Split-Path -Parent $PSScriptRoot

function Test-Docker { cmd /c 'docker info >nul 2>&1'; return $LASTEXITCODE -eq 0 }

function Start-DockerDesktop {
    if (Test-Docker) { return }
    cmd /c 'docker desktop start >nul 2>&1'
    $deadline = (Get-Date).AddMinutes(5)
    while (-not (Test-Docker)) {
        if ((Get-Date) -gt $deadline) { throw 'Docker did not start. Open Docker Desktop and retry.' }
        Start-Sleep -Seconds 5
    }
}

# Compose refuses to run any command until the password variable exists
function Initialize-EnvFile {
    $file = Join-Path $Root '.env'
    if (Test-Path -LiteralPath $file) { return }
    $password = [guid]::NewGuid().ToString('N')
    Set-Content -LiteralPath $file -Value "POSTGRES_PASSWORD=$password" -Encoding ascii
    Write-Host 'Created .env with a random local database password (git-ignored).'
}

function Test-Container([string]$Name) {
    $names = docker ps --format '{{.Names}}'
    return $names -contains $Name
}

if ($Mode -ne 'status') { Initialize-EnvFile }

switch ($Mode) {
    'dev' {
        Start-DockerDesktop
        if (Test-Container $Profile_) { minikube stop -p $Profile_ }
        docker compose --project-directory $Root up -d --wait postgres redis
        if ($LASTEXITCODE -ne 0) { throw 'Postgres or Redis did not start' }
    }
    'cluster' {
        Start-DockerDesktop
        docker compose --project-directory $Root --profile app stop
        minikube start -p $Profile_ --driver=docker --cni=calico --cpus=4 "--memory=$NodeMemoryMb" `
            --disk-size=20g --addons=metrics-server,ingress
        if ($LASTEXITCODE -ne 0) { throw 'minikube start failed' }
        # minikube cannot resize an existing node, so set the container limit directly
        docker update --memory "${NodeMemoryMb}m" --memory-swap "${NodeMemoryMb}m" $Profile_ | Out-Null
        kubectl config use-context $Profile_
    }
    'stop' {
        if (Test-Docker) {
            docker compose --project-directory $Root --profile app stop
            if (Test-Container $Profile_) { minikube stop -p $Profile_ }
        }
        Write-Host 'Project containers stopped. Quit Docker Desktop to release the WSL memory.'
    }
    'status' {
        Get-CimInstance Win32_OperatingSystem | ForEach-Object {
            'Windows memory free: {0:N1} of {1:N1} GB' -f ($_.FreePhysicalMemory / 1MB), ($_.TotalVisibleMemorySize / 1MB)
        }
        if (Test-Docker) {
            docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
        } else {
            'Docker is not running.'
        }
    }
}

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
$apiImage = "mall_api:offline"
$nginxImage = "mall_nginx:offline"
$baseImages = @(
    "python:3.11.15-slim-bookworm",
    "nginx:1.27.5-alpine",
    "mysql:8.0.45",
    "redis:7.4.8-alpine"
)

function Test-ImageExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    docker image inspect $Image *> $null
    return $LASTEXITCODE -eq 0
}

function Invoke-DockerBuild {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Dockerfile,
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    docker build -f $Dockerfile -t $Image .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to build $Image."
        exit 1
    }
}

Push-Location $repoRoot
try {
    $missingBaseImages = @()
    foreach ($image in $baseImages) {
        if (-not (Test-ImageExists -Image $image)) {
            $missingBaseImages += $image
        }
    }

    if ($missingBaseImages.Count -gt 0) {
        Write-Host "Missing base images required before local offline build:"
        foreach ($image in $missingBaseImages) {
            Write-Host "  - $image"
        }
        Write-Host "Cannot continue build."
        Write-Host "Prepare these images first with docker pull on a connected machine or docker load from a tar archive."
        Write-Host "You can inspect the current state with: powershell -ExecutionPolicy Bypass -File .\\deploy\\scripts\\check_offline_prereqs.ps1"
        exit 1
    }

    Write-Host "Building $apiImage from services/api/Dockerfile..."
    Invoke-DockerBuild -Dockerfile "services/api/Dockerfile" -Image $apiImage

    Write-Host "Building $nginxImage from deploy/docker/nginx/Dockerfile..."
    Invoke-DockerBuild -Dockerfile "deploy/docker/nginx/Dockerfile" -Image $nginxImage

    Write-Host "Offline business images built successfully."
    Write-Host "Next: powershell -ExecutionPolicy Bypass -File .\\deploy\\scripts\\export_images.ps1"
}
finally {
    Pop-Location
}

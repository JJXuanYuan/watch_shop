$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
$apiImage = "mall_api:offline"
$nginxImage = "mall_nginx:offline"

Push-Location $repoRoot
try {
    Write-Host "Building $apiImage from services/api/Dockerfile..."
    docker build -f services/api/Dockerfile -t $apiImage .

    Write-Host "Building $nginxImage from deploy/docker/nginx/Dockerfile..."
    docker build -f deploy/docker/nginx/Dockerfile -t $nginxImage .

    Write-Host "Offline business images built successfully."
    Write-Host "Next: powershell -ExecutionPolicy Bypass -File .\\deploy\\scripts\\export_images.ps1"
}
finally {
    Pop-Location
}

$ErrorActionPreference = "Stop"

param(
    [string]$OutputTar = "mall_offline_bundle.tar"
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")

$images = @(
    "mysql:8.0.45",
    "redis:7.4.8-alpine",
    "mall_api:offline",
    "mall_nginx:offline"
)

$baseImages = @(
    "mysql:8.0.45",
    "redis:7.4.8-alpine"
)

$localImages = @(
    "mall_api:offline",
    "mall_nginx:offline"
)

Push-Location $repoRoot
try {
    Write-Host "Pulling base images required by docker-compose.offline.yml..."
    foreach ($image in $baseImages) {
        Write-Host "-> docker pull $image"
        docker pull $image
    }

    foreach ($image in $localImages) {
        docker image inspect $image *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Missing local image: $image. Run deploy/scripts/build_offline_images.ps1 first."
        }
    }

    Write-Host "Saving images to $OutputTar ..."
    docker save -o $OutputTar $images

    Write-Host "Full offline image bundle exported successfully: $OutputTar"
    Write-Host "The bundle already includes the prebuilt mall_api and mall_nginx image layers."
    Write-Host "Upload this file to /opt/mall on the target server before running load_images_and_start.sh."
}
finally {
    Pop-Location
}

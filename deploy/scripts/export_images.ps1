$ErrorActionPreference = "Stop"

param(
    [string]$OutputTar = "mall_offline_bundle.tar"
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")

$requiredImages = @(
    "mysql:8.0.45",
    "redis:7.4.8-alpine",
    "mall_api:offline",
    "mall_nginx:offline"
)

function Test-ImageExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    docker image inspect $Image *> $null
    return $LASTEXITCODE -eq 0
}

Push-Location $repoRoot
try {
    $missingImages = @()
    foreach ($image in $requiredImages) {
        if (-not (Test-ImageExists -Image $image)) {
            $missingImages += $image
        }
    }

    if ($missingImages.Count -gt 0) {
        Write-Host "Cannot export an offline bundle because these images are missing:"
        foreach ($image in $missingImages) {
            Write-Host "  - $image"
        }
        Write-Host "Do not continue export until the missing images are prepared."
        Write-Host "Use a connected machine to docker pull them, or docker load them from a tar archive first."
        Write-Host "You can inspect the current state with: powershell -ExecutionPolicy Bypass -File .\\deploy\\scripts\\check_offline_prereqs.ps1"
        exit 1
    }

    Write-Host "Saving images to $OutputTar ..."
    docker save -o $OutputTar $requiredImages
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to export offline bundle: $OutputTar"
        exit 1
    }

    Write-Host "Full offline image bundle exported successfully: $OutputTar"
    Write-Host "The bundle already includes the prebuilt mall_api and mall_nginx image layers."
    Write-Host "Upload this file to /opt/mall on the target server before running load_images_and_start.sh."
}
finally {
    Pop-Location
}

$ErrorActionPreference = "Stop"

$baseImages = @(
    "python:3.11.15-slim-bookworm",
    "nginx:1.27.5-alpine",
    "mysql:8.0.45",
    "redis:7.4.8-alpine"
)

$businessImages = @(
    "mall_api:offline",
    "mall_nginx:offline"
)

$existingBase = New-Object System.Collections.Generic.List[string]
$missingBase = New-Object System.Collections.Generic.List[string]
$existingBusiness = New-Object System.Collections.Generic.List[string]
$missingBusiness = New-Object System.Collections.Generic.List[string]

function Test-ImageExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    docker image inspect $Image *> $null
    return $LASTEXITCODE -eq 0
}

function Write-ImageGroup {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.List[string]]$Images
    )

    Write-Host $Title
    if ($Images.Count -eq 0) {
        Write-Host "  - none"
        return
    }

    foreach ($image in $Images) {
        Write-Host "  - $image"
    }
}

foreach ($image in $baseImages) {
    if (Test-ImageExists -Image $image) {
        $existingBase.Add($image)
    }
    else {
        $missingBase.Add($image)
    }
}

foreach ($image in $businessImages) {
    if (Test-ImageExists -Image $image) {
        $existingBusiness.Add($image)
    }
    else {
        $missingBusiness.Add($image)
    }
}

Write-ImageGroup -Title "[existing base images]" -Images $existingBase
Write-ImageGroup -Title "[missing base images]" -Images $missingBase
Write-ImageGroup -Title "[existing business images]" -Images $existingBusiness
Write-ImageGroup -Title "[missing business images]" -Images $missingBusiness

Write-Host ""
if ($missingBase.Count -gt 0) {
    Write-Host "Base images are missing. Cannot continue build or export."
    Write-Host "Prepare the missing base images first with docker pull on a connected machine or docker load from a tar archive."
    exit 1
}

if ($missingBusiness.Count -gt 0) {
    Write-Host "Base images are ready, but business images are still missing."
    Write-Host "You can continue build after the base images are ready, but export cannot continue until mall_api:offline and mall_nginx:offline exist."
    exit 2
}

Write-Host "All offline prerequisites are ready. You can continue build and export."

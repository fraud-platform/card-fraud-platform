# Docker Full Import Script (Fixed for tar.gz volume names)

$ErrorActionPreference = "Stop"

# -------------------------------
# 0. Check Docker
# -------------------------------
try {
    docker info | Out-Null
} catch {
    Write-Host "Docker is not running. Start Docker Desktop." -ForegroundColor Red
    exit 1
}

# -------------------------------
# 1. Locate backup file
# -------------------------------
$BackupFile = "$env:USERPROFILE\Downloads\docker-full-backup.tar"

if (!(Test-Path $BackupFile)) {
    Write-Host "Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "Using backup: $BackupFile" -ForegroundColor Cyan

# -------------------------------
# 2. Prepare clean import folder
# -------------------------------
$ImportDir = "$env:USERPROFILE\docker-import"

Write-Host "`n[1/4] Preparing clean workspace..." -ForegroundColor Yellow

if (Test-Path $ImportDir) {
    Write-Host "  Removing old import directory..."
    Remove-Item -Recurse -Force $ImportDir
}

New-Item -ItemType Directory -Path $ImportDir | Out-Null

# -------------------------------
# 3. Extract backup
# -------------------------------
Write-Host "[2/4] Extracting backup..." -ForegroundColor Yellow

$backupPath = (Resolve-Path $BackupFile).Path -replace '\\','/'

docker run --rm `
  -v "${ImportDir}:/data" `
  -v "${backupPath}:/backup.tar" `
  alpine tar xf /backup.tar -C /data

Write-Host "  Extraction complete." -ForegroundColor Green

# -------------------------------
# 4. Load images
# -------------------------------
Write-Host "[3/4] Loading Docker images..." -ForegroundColor Yellow

$imagesTar = "$ImportDir\images\all-images.tar"

if (Test-Path $imagesTar) {
    docker load -i $imagesTar
    Write-Host "  Images loaded." -ForegroundColor Green
} else {
    Write-Host "  No images tar found, skipping." -ForegroundColor Yellow
}

# -------------------------------
# 5. Restore volumes
# -------------------------------
Write-Host "[4/4] Restoring volumes..." -ForegroundColor Yellow

$tarFiles = Get-ChildItem "$ImportDir\volumes\*" -Include *.tar,*.tar.gz -ErrorAction SilentlyContinue

foreach ($tar in $tarFiles) {
    if ($tar.Length -lt 1024) {
        Write-Host "  Skipping corrupted: $($tar.Name)" -ForegroundColor Red
        continue
    }

    $volName = $tar.Name -replace '\.tar\.gz$','' -replace '\.tar$',''
    Write-Host "  -> Restoring $volName"

    $volumeExists = docker volume inspect $volName *> $null
    if ($volumeExists -eq 0) {
        docker volume rm $volName *> $null | Out-Null
    }

    docker volume create $volName | Out-Null

    if ($volName -like "*postgres*") {
        Write-Host "    (Postgres safe mode)"

        docker run --rm `
          -v "${volName}:/target" `
          -v "$($ImportDir)\volumes:/backup:ro" `
          alpine sh -c "
            cd /target &&
            tar xzf /backup/$($tar.Name) \
              --exclude='*/pg_logical/*' \
              --exclude='*/pg_replslot/*' \
              --exclude='*/pg_dynshmem/*'
          "
    } else {
        docker run --rm `
          -v "${volName}:/target" `
          -v "$($ImportDir)\volumes:/backup:ro" `
          alpine sh -c "cd /target && tar xzf /backup/$($tar.Name)"
    }
}

Write-Host "  Done." -ForegroundColor Green

# -------------------------------
# 6. Summary
# -------------------------------
Write-Host ""
Write-Host "Import completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host ("Images:  " + (docker images -q).Count)
Write-Host ("Volumes: " + (docker volume ls -q).Count)

<#
.SYNOPSIS
  Chay backend (FastAPI/uvicorn) va frontend (Next.js) cung luc, log gop vao 1 cua so.

.DESCRIPTION
  Harness dev dung chung cho team (chi Windows). Moi service la 1 process rieng (khong
  dung PowerShell Job) vi uvicorn --reload va "npm run dev" -> "next dev" -> node deu tu
  fork them process con; Stop-Job/Remove-Job KHONG giet duoc cac process con do, de lai
  cong 3000/8000 bi chiem vinh vien. O day dung Start-Process -PassThru de lay PID goc
  that, roi taskkill /T /F PID do khi thoat de giet ca cay process.

.PARAMETER BackendOnly
  Chi chay backend (uvicorn --reload tren :8000).

.PARAMETER FrontendOnly
  Chi chay frontend (next dev tren :3000).

.EXAMPLE
  .\dev.ps1
.EXAMPLE
  .\dev.ps1 -BackendOnly
#>
param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

$uvicorn = Join-Path $root '.venv\Scripts\uvicorn.exe'
if (-not (Test-Path $uvicorn)) {
    Write-Host "Khong thay $uvicorn - chay 'python -m venv .venv' va 'pip install -r requirements.txt' truoc." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $root 'web-next\node_modules'))) {
    Write-Host "Khong thay web-next\node_modules - chay 'npm install' trong web-next truoc." -ForegroundColor Red
    exit 1
}

$logDir = Join-Path $env:TEMP 'vnutricare-dev'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$procs = @()   # danh sach @{ Name; Process; OutFile; ErrFile; Offset }

function Start-DevService {
    param([string]$Name, [string]$FilePath, [string[]]$ArgList, [string]$WorkDir)
    $outFile = Join-Path $logDir "$Name.out.log"
    $errFile = Join-Path $logDir "$Name.err.log"
    Remove-Item $outFile,$errFile -ErrorAction SilentlyContinue
    New-Item -ItemType File -Path $outFile,$errFile -Force | Out-Null
    $proc = Start-Process -FilePath $FilePath -ArgumentList $ArgList -WorkingDirectory $WorkDir `
        -RedirectStandardOutput $outFile -RedirectStandardError $errFile -WindowStyle Hidden -PassThru
    return @{ Name = $Name; Process = $proc; OutFile = $outFile; ErrFile = $errFile; OutOffset = 0; ErrOffset = 0 }
}

if (-not $FrontendOnly) {
    Write-Host "[backend] starting (PID sau khi spawn se in ben duoi) - http://localhost:8000" -ForegroundColor Cyan
    $procs += Start-DevService -Name 'backend' -FilePath $uvicorn `
        -ArgList @('src.main:app','--reload','--host','0.0.0.0','--port','8000') -WorkDir $root
}
if (-not $BackendOnly) {
    Write-Host "[frontend] starting - http://localhost:3000" -ForegroundColor Green
    # npm.cmd la batch script - chay qua cmd.exe /c de Start-Process bat dung toan bo cay
    # con (npm-cli.js -> next dev -> node server) duoi 1 PID goc de sau nay taskkill /T.
    $procs += Start-DevService -Name 'frontend' -FilePath 'cmd.exe' `
        -ArgList @('/c','npm run dev') -WorkDir (Join-Path $root 'web-next')
}

$colors = @{ backend = 'Cyan'; frontend = 'Green' }

function Write-NewLines {
    param($svc)
    foreach ($pair in @(@{ File = $svc.OutFile; Key = 'OutOffset' }, @{ File = $svc.ErrFile; Key = 'ErrOffset' })) {
        $lines = Get-Content -Path $pair.File -ErrorAction SilentlyContinue
        if ($null -eq $lines) { continue }
        if ($lines -isnot [array]) { $lines = @($lines) }
        $offset = $svc[$pair.Key]
        if ($lines.Count -gt $offset) {
            for ($i = $offset; $i -lt $lines.Count; $i++) {
                Write-Host "[$($svc.Name)] $($lines[$i])" -ForegroundColor $colors[$svc.Name]
            }
            $svc[$pair.Key] = $lines.Count
        }
    }
}

try {
    while ($true) {
        $anyAlive = $false
        foreach ($svc in $procs) {
            Write-NewLines -svc $svc
            if (-not $svc.Process.HasExited) { $anyAlive = $true }
        }
        if (-not $anyAlive) {
            Write-Host "Ca hai service da dung (crash hoac exit)." -ForegroundColor Yellow
            break
        }
        Start-Sleep -Milliseconds 300
    }
}
finally {
    Write-Host "Stopping..." -ForegroundColor Yellow
    foreach ($svc in $procs) {
        if (-not $svc.Process.HasExited) {
            & taskkill /PID $svc.Process.Id /T /F 2>$null | Out-Null
        }
    }
}

# Install git pre-push hook for AI log submission (Windows PowerShell).
# Run once after cloning: powershell -ExecutionPolicy Bypass -File scripts\setup_hooks.ps1

$ErrorActionPreference = 'Stop'

$HookFile = '.git/hooks/pre-push'

# Git on Windows runs hooks via Git Bash, so the hook body must be bash.
$HookBody = @'
#!/bin/sh
# Pre-push: sweep recent Codex and Antigravity prompts, then submit AI logs.
bash scripts/_pyrun.sh scripts/log_codex.py --auto || true
bash scripts/_pyrun.sh scripts/log_antigravity.py --auto || true
bash scripts/_pyrun.sh scripts/submit_log.py || true
exit 0
'@

# Windows PowerShell's UTF8 encoding includes a BOM. Git cannot parse a
# shebang when the file starts with that BOM, so write UTF-8 without BOM and
# normalize line endings to LF.
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$HookBody = $HookBody -replace "`r`n", "`n"
[System.IO.File]::WriteAllText((Join-Path (Get-Location) $HookFile), $HookBody, $Utf8NoBom)
Write-Host "[ai-log] Git pre-push hook installed."

if (-not (Test-Path .ai-log)) { New-Item -ItemType Directory -Path .ai-log | Out-Null }
if (-not (Test-Path .ai-log/.gitkeep)) { New-Item -ItemType File -Path .ai-log/.gitkeep | Out-Null }

Write-Host "[ai-log] Setup complete. Configure AI_LOG_SERVER in your .env file."

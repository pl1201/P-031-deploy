@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
REM Cross-platform Python launcher for AI log hooks (Windows cmd.exe).
REM Prefer the active/repo virtual environment, then try py -3 -> python -> python3.
REM Exits 0 silently if no Python is found - hooks must never block the AI tool.

for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
  if exist "%%D\python.exe" (
    "%%D\python.exe" %*
    exit /b
  )
)

if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
  "%VIRTUAL_ENV%\Scripts\python.exe" %*
  if not errorlevel 1 exit /b 0
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" %*
  if not errorlevel 1 exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 %*
  if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  python %*
  if not errorlevel 1 exit /b 0
)

where python3 >nul 2>nul
if not errorlevel 1 (
  python3 %*
  exit /b %ERRORLEVEL%
)

exit /b 0

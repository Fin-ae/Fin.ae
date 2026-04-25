@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\.."

if exist "%REPO_ROOT%\backend\venv\Scripts\python.exe" (
  "%REPO_ROOT%\backend\venv\Scripts\python.exe" "%SCRIPT_DIR%import_department_json.py" %*
) else (
  wsl bash -lc "cd /mnt/g/dem/Finae && source backend/venv/bin/activate && python3 backend/scripts/import_department_json.py %*"
)

endlocal

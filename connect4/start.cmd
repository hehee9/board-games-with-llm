@echo off
setlocal
set "PROJECT_DIR=%~dp0."
uv run --project "%PROJECT_DIR%" connect4 start %*
exit /b %ERRORLEVEL%

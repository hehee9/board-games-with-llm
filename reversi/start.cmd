@echo off
setlocal
set "PROJECT_DIR=%~dp0."
uv run --project "%PROJECT_DIR%" reversi start %*
exit /b %ERRORLEVEL%

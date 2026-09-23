@echo off
set "ROOT_DIR=%~dp0"
set "PYTHONPATH=%ROOT_DIR%src;%PYTHONPATH%"

py -m shell_emulator %*
exit /b %ERRORLEVEL%

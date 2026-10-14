@echo off
cd /d "%~dp0"
py -3 -m cdvector
if errorlevel 1 pause

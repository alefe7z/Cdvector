@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python -m pip install pyinstaller==6.16.0
if errorlevel 1 exit /b 1
.venv\Scripts\python -m PyInstaller --noconfirm --clean --onefile --windowed --name cdvector launcher.py
if errorlevel 1 exit /b 1
echo Executavel criado em dist\cdvector.exe
pause

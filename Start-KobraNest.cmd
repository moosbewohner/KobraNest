@echo off
setlocal
cd /d "%~dp0"
if exist KobraNest-Assistent.exe (
  KobraNest-Assistent.exe
  goto finished
)
if exist Kobrian-Assistent.exe (
  Kobrian-Assistent.exe
  goto finished
)
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -c "import paramiko" >nul 2>nul
if errorlevel 1 goto dependencies
py -3 assistant.py
goto finished
:usepython
where python >nul 2>nul
if errorlevel 1 goto missing
python -c "import paramiko" >nul 2>nul
if errorlevel 1 goto dependencies
python assistant.py
goto finished
:dependencies
echo Python gefunden, aber Paramiko fehlt.
echo Einmalig im Paketordner ausfuehren: python -m pip install -r requirements.txt
goto finished
:missing
echo Bitte Python 3.10 oder neuer installieren, danach requirements.txt installieren.
:finished
pause

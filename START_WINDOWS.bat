@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0" || exit /b 1

REM uv, Python, кеши и временные файлы размещаются в папке проекта.
set "UV_UNMANAGED_INSTALL=%CD%\.runtime\uv"
set "UV_PYTHON_INSTALL_DIR=%CD%\.runtime\python"
set "UV_PYTHON_NO_REGISTRY=1"
set "UV_CACHE_DIR=%CD%\.runtime\cache\uv"
set "PIP_CACHE_DIR=%CD%\.runtime\cache\pip"
set "PIP_CONFIG_FILE=NUL"
set "TEMP=%CD%\.runtime\tmp"
set "TMP=%TEMP%"
if not exist "%TEMP%" mkdir "%TEMP%"

REM uv загружает Python; этот Python создаёт окружение с pip.
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
if not exist ".runtime\uv\uv.exe" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression" || goto ERROR
".runtime\uv\uv.exe" --no-config python install 3.12 --no-bin || goto ERROR
".runtime\uv\uv.exe" --no-config python find 3.12 --managed-python --no-project >".runtime\python-path.txt" || goto ERROR
set /p BASE_PY=<".runtime\python-path.txt"
if not exist ".venv\Scripts\python.exe" "%BASE_PY%" -I -X utf8 -m venv .venv || goto ERROR
echo Подготовка библиотек...
".venv\Scripts\python.exe" -I -X utf8 -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto ERROR

REM Streamlit открывает браузер; приветствие с кодами цвета отключено.
echo Адрес приложения: http://127.0.0.1:8501 — для остановки нажмите Ctrl+C.
".venv\Scripts\python.exe" -I -X utf8 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 ^
    --server.headless false --server.showEmailPrompt false --browser.serverAddress 127.0.0.1 ^
    --browser.gatherUsageStats false --logger.hideWelcomeMessage true || goto ERROR
exit /b 0

:ERROR
echo Не удалось запустить приложение. Прочитайте сообщение выше.
pause
exit /b 1

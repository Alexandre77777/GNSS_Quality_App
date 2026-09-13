@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0" || exit /b 1

REM uv, Python, кеши и временные файлы размещаются в папке проекта.
set "UV_UNMANAGED_INSTALL=%CD%\.runtime\uv"
set "UV_PYTHON_INSTALL_DIR=%CD%\.runtime\python"
set "UV_PYTHON_NO_REGISTRY=1"
set "UV_CACHE_DIR=%CD%\.runtime\cache\uv"
set "UV_INSECURE_HOST="
set "PIP_CACHE_DIR=%CD%\.runtime\cache\pip"
set "PIP_CONFIG_FILE=NUL"
set "PIP_EXTRA_INDEX_URL="
set "PIP_TRUSTED_HOST="
set "TEMP=%CD%\.runtime\tmp"
set "TMP=%TEMP%"
if not exist "%TEMP%" mkdir "%TEMP%"

REM Windows 10/11: curl или PowerShell; для каждого способа доступны astral.sh и GitHub.
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
if not exist ".runtime\uv\uv.exe" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Write-Host 'Загрузка uv: GitHub / TLS 1.2'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing https://github.com/astral-sh/uv/releases/latest/download/uv-installer.ps1 -TimeoutSec 60 -OutFile '.runtime\tmp\uv-install.ps1'"
    if errorlevel 1 powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Write-Host 'Резервная загрузка: astral.sh / TLS 1.2'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing https://astral.sh/uv/install.ps1 -TimeoutSec 60 -OutFile '.runtime\tmp\uv-install.ps1'"
    if errorlevel 1 "%SystemRoot%\System32\curl.exe" --fail --location --silent --show-error --retry 2 --connect-timeout 15 --max-time 60 https://astral.sh/uv/install.ps1 --output ".runtime\tmp\uv-install.ps1"
    if errorlevel 1 "%SystemRoot%\System32\curl.exe" --fail --location --silent --show-error --retry 2 --connect-timeout 15 --max-time 60 https://github.com/astral-sh/uv/releases/latest/download/uv-installer.ps1 --output ".runtime\tmp\uv-install.ps1" || goto ERROR
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; & '.\.runtime\tmp\uv-install.ps1'" || goto ERROR
)

REM uv загружает Python; этот Python создаёт окружение с pip.
".runtime\uv\uv.exe" --no-config python install 3.12 --no-bin || goto ERROR
".runtime\uv\uv.exe" --no-config python find 3.12 --managed-python --no-project >".runtime\python-path.txt" || goto ERROR
set /p BASE_PY=<".runtime\python-path.txt"
if not exist ".venv\Scripts\python.exe" "%BASE_PY%" -I -X utf8 -m venv .venv || goto ERROR
echo Подготовка библиотек...
REM При ошибке PyPI пробуем два HTTPS-зеркала; версии берем из requirements.txt.
for %%I in (https://pypi.org/simple https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple https://repo.huaweicloud.com/repository/pypi/simple) do (
    echo Источник библиотек: %%I
    ".venv\Scripts\python.exe" -I -X utf8 -m pip install --disable-pip-version-check --progress-bar off --timeout 30 --retries 2 --index-url %%I --log ".runtime\install.log" -r requirements.txt
    if not errorlevel 1 goto READY
)
REM Если pip не смог скачать пакеты, используем сетевой механизм уже установленного uv.
set "UV_HTTP_TIMEOUT=30"
set "UV_HTTP_RETRIES=2"
for %%I in (https://pypi.org/simple https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple https://repo.huaweicloud.com/repository/pypi/simple) do (
    echo Резервная установка через uv: %%I
    ".runtime\uv\uv.exe" --no-config pip install --python ".venv\Scripts\python.exe" --default-index %%I --color never -r requirements.txt >>".runtime\install.log" 2>&1
    if not errorlevel 1 goto READY
)
REM Последний резерв: отключаем проверку сертификатов только для серверов пакетов.
echo ВНИМАНИЕ: все защищенные попытки не удались. Проверка сертификатов серверов пакетов будет отключена.
echo Этот режим не защищает от подмены пакетов. Используйте доверенное подключение к сети.
set "UV_INSECURE_HOST=pypi.org files.pythonhosted.org mirrors.tuna.tsinghua.edu.cn repo.huaweicloud.com"
for %%I in (https://pypi.org/simple https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple https://repo.huaweicloud.com/repository/pypi/simple) do (
    echo Последний резерв без проверки сертификатов: %%I
    ".runtime\uv\uv.exe" --no-config pip install --python ".venv\Scripts\python.exe" --default-index %%I --color never -r requirements.txt >>".runtime\install.log" 2>&1
    if not errorlevel 1 goto READY
)
goto ERROR

:READY
set "UV_INSECURE_HOST="
".venv\Scripts\python.exe" -I -X utf8 -m pip check || goto ERROR

REM Streamlit открывает браузер; приветствие с кодами цвета отключено.
echo Адрес приложения: http://127.0.0.1:8501 — для остановки нажмите Ctrl+C.
".venv\Scripts\python.exe" -I -X utf8 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 ^
    --server.headless false --server.showEmailPrompt false --browser.serverAddress 127.0.0.1 ^
    --browser.gatherUsageStats false --logger.hideWelcomeMessage true || goto ERROR
exit /b 0

:ERROR
echo Не удалось запустить приложение. Прочитайте сообщение выше.
if exist ".runtime\install.log" echo Журнал установки библиотек: %CD%\.runtime\install.log
pause
exit /b 1

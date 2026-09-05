#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"

# uv, Python, кеши и временные файлы размещаются в папке проекта.
export UV_UNMANAGED_INSTALL="$PWD/.runtime/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/.runtime/python"
export UV_CACHE_DIR="$PWD/.runtime/cache/uv"
export PIP_CACHE_DIR="$PWD/.runtime/cache/pip"
export PIP_CONFIG_FILE=/dev/null
export TMPDIR="$PWD/.runtime/tmp"
mkdir -p "$TMPDIR"

# uv загружает Python; этот Python создаёт окружение с pip.
if [ ! -x .runtime/uv/uv ]; then
    curl -fLsS https://astral.sh/uv/install.sh -o "$TMPDIR/install-uv.sh"
    sh "$TMPDIR/install-uv.sh"
fi
.runtime/uv/uv --no-config python install 3.12 --no-bin
BASE_PY=$(.runtime/uv/uv --no-config python find 3.12 --managed-python --no-project)
if [ ! -x .venv/bin/python ]; then
    "$BASE_PY" -I -X utf8 -m venv .venv
fi
echo "Подготовка библиотек..."
.venv/bin/python -I -X utf8 -m pip install --quiet --disable-pip-version-check -r requirements.txt

# Streamlit открывает браузер; приветствие с кодами цвета отключено.
echo "Адрес приложения: http://127.0.0.1:8501 — для остановки нажмите Ctrl+C."
.venv/bin/python -I -X utf8 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 \
    --server.headless false --server.showEmailPrompt false --browser.serverAddress 127.0.0.1 \
    --browser.gatherUsageStats false --logger.hideWelcomeMessage true

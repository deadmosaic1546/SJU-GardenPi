#!/usr/bin/env bash
set -euo pipefail

# Install the Garden Web UI
# Run this script from the project root

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root."
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

APP_NAME="garden-web"
APP_USER="gardenweb"
APP_GROUP="gardenweb"
SHARED_GROUP="picos"

APP_DIR="/usr/local/lib/${APP_NAME}"
APP_BIN_DIR="${APP_DIR}/bin"
VENV_DIR="${APP_DIR}/.venv"

ETC_DIR="/etc/${APP_NAME}"
VAR_DIR="/var/lib/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"

SERVICE_NAME="${APP_NAME}.service"
SERVICE_SRC="${PROJECT_ROOT}/docs/${SERVICE_NAME}"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"

CLUSTER_VAR_DIR="/var/lib/garden"

echo "[*] Installing system dependencies..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-venv python3-pip rsync
elif command -v pacman >/dev/null 2>&1; then
  pacman -Sy --noconfirm \
    python python-pip rsync
else
  echo "[!] Unsupported distro: no apt-get or pacman found."
  exit 1
fi

echo "[*] Creating groups/users..."
getent group "${SHARED_GROUP}" >/dev/null || groupadd -r "${SHARED_GROUP}"
getent group "${APP_GROUP}" >/dev/null || groupadd -r "${APP_GROUP}"

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd \
    -r \
    -g "${APP_GROUP}" \
    -G "${SHARED_GROUP}" \
    -s /usr/sbin/nologin \
    -d "${VAR_DIR}" \
    -M \
    "${APP_USER}"
fi

echo "[*] Creating directories..."
install -d -m 0755 /usr/local/bin
install -d -m 0755 -o root -g root "${APP_DIR}"
install -d -m 0755 -o root -g root "${APP_BIN_DIR}"
install -d -m 0750 -o root -g "${APP_GROUP}" "${ETC_DIR}"
install -d -m 0750 -o "${APP_USER}" -g "${APP_GROUP}" "${VAR_DIR}"
install -d -m 0750 -o "${APP_USER}" -g "${APP_GROUP}" "${LOG_DIR}"

echo "[*] Installing application code..."
rsync -a \
  --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude 'build' \
  --exclude 'instance' \
  --exclude 'test.db' \
  "${PROJECT_ROOT}/flaskr/" "${APP_DIR}/flaskr/"

chown -R root:root "${APP_DIR}"
find "${APP_DIR}" -type d -exec chmod 0755 {} \;
find "${APP_DIR}" -type f -exec chmod 0644 {} \;

echo "[*] Installing writable app database..."
if [[ -f "${PROJECT_ROOT}/build/auth.db" ]]; then
  install -m 0640 -o "${APP_USER}" -g "${APP_GROUP}" \
    "${PROJECT_ROOT}/build/auth.db" \
    "${VAR_DIR}/auth.db"
elif [[ -f "${PROJECT_ROOT}/test.db" ]]; then
  install -m 0640 -o "${APP_USER}" -g "${APP_GROUP}" \
    "${PROJECT_ROOT}/test.db" \
    "${VAR_DIR}/auth.db"
else
  echo "[*] No auth DB seed file found; creating empty placeholder."
  touch "${VAR_DIR}/auth.db"
  chown "${APP_USER}:${APP_GROUP}" "${VAR_DIR}/auth.db"
  chmod 0640 "${VAR_DIR}/auth.db"
fi

echo "[*] Installing environment template..."
if [[ -f "${PROJECT_ROOT}/env-REF.txt" && ! -f "${ETC_DIR}/${APP_NAME}.env" ]]; then
  install -m 0640 -o root -g "${APP_GROUP}" \
    "${PROJECT_ROOT}/env-REF.txt" \
    "${ETC_DIR}/${APP_NAME}.env"
fi

echo "[*] Writing default environment file if missing..."
if [[ ! -f "${ETC_DIR}/${APP_NAME}.env" ]]; then
  cat > "${ETC_DIR}/${APP_NAME}.env" <<EOF
FLASK_APP=flaskr
FLASK_ENV=production
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
GARDEN_AUTH_DB=${VAR_DIR}/auth.db
GARDEN_CLUSTER_DB=${CLUSTER_VAR_DIR}/plot.db
EOF
  chown root:${APP_GROUP} "${ETC_DIR}/${APP_NAME}.env"
  chmod 0640 "${ETC_DIR}/${APP_NAME}.env"
fi

echo "[*] Creating Python virtual environment..."
python3 -m venv "${VENV_DIR}"
chmod +x "${VENV_DIR}/bin/pip"
chmod +x "${VENV_DIR}/bin/pip3"
chmod +x "${VENV_DIR}/bin/pip3.13"
"${VENV_DIR}/bin/pip" install --upgrade pip wheel
"${VENV_DIR}/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt"

echo "[*] Creating launcher..."
cat > "${APP_BIN_DIR}/${APP_NAME}" <<EOF
#!/usr/bin/env bash
set -euo pipefail

export FLASK_APP="\${FLASK_APP:-flaskr}"
export FLASK_ENV="\${FLASK_ENV:-production}"
export FLASK_RUN_HOST="\${FLASK_RUN_HOST:-0.0.0.0}"
export FLASK_RUN_PORT="\${FLASK_RUN_PORT:-8080}"

exec "${VENV_DIR}/bin/python" -m flask --app "\${FLASK_APP}" run --host="\${FLASK_RUN_HOST}" --port="\${FLASK_RUN_PORT}"
EOF

chown root:root "${APP_BIN_DIR}/${APP_NAME}"
chmod 0755 "${APP_BIN_DIR}/${APP_NAME}"

ln -sf "${APP_BIN_DIR}/${APP_NAME}" "/usr/local/bin/${APP_NAME}"

mkdir -m "${APP_DIR}/instance"

echo "[*] Ensuring cluster DB permissions allow shared-group read access..."
if [[ -d "${CLUSTER_VAR_DIR}" ]]; then
  chgrp "${SHARED_GROUP}" "${CLUSTER_VAR_DIR}" || true
  chmod 0750 "${CLUSTER_VAR_DIR}" || true

  find "${CLUSTER_VAR_DIR}" -type f -exec chgrp "${SHARED_GROUP}" {} \; || true
  find "${CLUSTER_VAR_DIR}" -type f -exec chmod 0640 {} \; || true
fi

echo "[*] Installing systemd service..."
if [[ ! -f "${SERVICE_SRC}" ]]; then
  echo "[!] Missing ${SERVICE_NAME} in project root."
  exit 1
fi

install -m 0644 "${SERVICE_SRC}" "${SERVICE_DST}"

echo "[*] Reloading and enabling service..."
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

echo
echo "[+] Installation complete."
echo "    Service: ${SERVICE_NAME}"
echo "    Logs:    journalctl -u ${SERVICE_NAME} -f"
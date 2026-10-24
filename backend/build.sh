#!/usr/bin/env bash
# Build step for hosting: Python deps, React build into frontend_dist/, static files, migrations.
# Run from the backend/ folder (Render's rootDir does this).
set -o errexit

FRONTEND_DIR="../EduNextSL Frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to build the React frontend (Node 20.19+ or 22.12+)." >&2
  exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

(cd "$FRONTEND_DIR" && npm ci && npm run build)

python manage.py collectstatic --no-input

# Schema changes need a direct (non-pooled) connection; the app itself runs on the pooled URL.
DATABASE_URL="${DIRECT_DATABASE_URL:-$DATABASE_URL}" python manage.py migrate --no-input
DATABASE_URL="${DIRECT_DATABASE_URL:-$DATABASE_URL}" python manage.py createcachetable

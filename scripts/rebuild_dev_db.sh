#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
LOCAL_APPS=(accounts orders threads todos)

echo "Stopping local Django dev server if it is running..."
pkill -f "manage.py runserver" 2>/dev/null || true

echo "Removing Python bytecode caches from project files..."
find . \
  \( -path "./.git" -o -path "./.venv" -o -path "./media" \) -prune -o \
  \( -type d -name "__pycache__" -o -type f \( -name "*.pyc" -o -name "*.pyo" \) \) \
  -exec rm -rf {} +

echo "Removing local SQLite database..."
rm -f db.sqlite3

echo "Removing local app migration files..."
for app in "${LOCAL_APPS[@]}"; do
  find "$app/migrations" -type f -name "*.py" ! -name "__init__.py" -delete
done

echo "Creating fresh initial migrations..."
"$PYTHON_BIN" manage.py makemigrations "${LOCAL_APPS[@]}"

echo "Applying migrations..."
"$PYTHON_BIN" manage.py migrate

echo "Loading mock data..."
"$PYTHON_BIN" manage.py seed_demo

echo "Development database rebuilt."

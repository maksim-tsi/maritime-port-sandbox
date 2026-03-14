#!/usr/bin/env bash
set -euo pipefail

EXPOSE_ADMIN_DOCS=1 \
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

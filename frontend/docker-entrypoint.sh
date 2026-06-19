#!/bin/sh
# Runs via nginx's /docker-entrypoint.d/ before the server starts.
# Writes the runtime API base URL the SPA reads, from API_BASE_URL (or VITE_API_BASE_URL).
: "${API_BASE_URL:=${VITE_API_BASE_URL:-/api/v1}}"
# Source link (kept visible for AGPL §13) and whether to show the "Powered by" footer badge.
: "${SOURCE_URL:=https://github.com/hjmacemail/lmsbridge}"
: "${SHOW_BRANDING:=true}"
cat > /usr/share/nginx/html/config.js <<CFG
window.__LMSBRIDGE_API__ = "${API_BASE_URL}";
window.__LMSBRIDGE_SOURCE__ = "${SOURCE_URL}";
window.__LMSBRIDGE_BRANDING__ = ${SHOW_BRANDING};
CFG

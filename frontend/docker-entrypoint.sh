#!/bin/sh
# Runs via nginx's /docker-entrypoint.d/ before the server starts.
# Bind nginx to the platform-provided port (Railway/Render inject $PORT); default 80 locally.
sed -i "s/listen  *80;/listen ${PORT:-80};/" /etc/nginx/conf.d/default.conf
# Writes the runtime API base URL the SPA reads, from API_BASE_URL (or VITE_API_BASE_URL).
: "${API_BASE_URL:=${VITE_API_BASE_URL:-/api/v1}}"
# Source link (kept visible for AGPL §13) and whether to show the "Powered by" footer badge.
: "${SOURCE_URL:=https://github.com/hjmacemail/lmsbridge}"
: "${SHOW_BRANDING:=true}"
# LMS Bridge marketing homepage (the "by LMS Bridge" link in Sage points here).
: "${HOME_URL:=https://www.lmsbridge.app}"
# Optional white-label branding for the Sage app (e.g. run an instance as "TWAS Learning").
# Set any of BRAND_NAME / BRAND_TAGLINE / BRAND_ACCENT (hex) / BRAND_LOGO_URL / BRAND_ATTRIBUTION.
# The AGPL "source" link always remains.
BRAND_JS="{"
[ -n "${BRAND_NAME}" ] && BRAND_JS="${BRAND_JS}\"name\":\"${BRAND_NAME}\","
[ -n "${BRAND_TAGLINE}" ] && BRAND_JS="${BRAND_JS}\"tagline\":\"${BRAND_TAGLINE}\","
[ -n "${BRAND_ACCENT}" ] && BRAND_JS="${BRAND_JS}\"accent\":\"${BRAND_ACCENT}\","
[ -n "${BRAND_LOGO_URL}" ] && BRAND_JS="${BRAND_JS}\"logoUrl\":\"${BRAND_LOGO_URL}\","
[ -n "${BRAND_ATTRIBUTION}" ] && BRAND_JS="${BRAND_JS}\"attribution\":\"${BRAND_ATTRIBUTION}\","
BRAND_JS="${BRAND_JS%,}}"
cat > /usr/share/nginx/html/config.js <<CFG
window.__LMSBRIDGE_API__ = "${API_BASE_URL}";
window.__LMSBRIDGE_SOURCE__ = "${SOURCE_URL}";
window.__LMSBRIDGE_BRANDING__ = ${SHOW_BRANDING};
window.__LMSBRIDGE_HOME__ = "${HOME_URL}";
window.__LMSBRIDGE_BRAND__ = ${BRAND_JS};
CFG

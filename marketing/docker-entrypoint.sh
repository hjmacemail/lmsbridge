#!/bin/sh
# Runs via nginx's /docker-entrypoint.d/ before the server starts.
# Bind nginx to the platform-provided port (Railway/Render inject $PORT); default 80 locally.
sed -i "s/listen  *80;/listen ${PORT:-80};/" /etc/nginx/conf.d/default.conf
# Injects the backend API base URL (lead form + LTI config) and the app URL (live-demo link).
: "${API_BASE_URL:=http://localhost:8000/api/v1}"
: "${APP_BASE_URL:=http://localhost:8080}"
# Public source repo for the "View source" / GitHub links.
: "${SOURCE_URL:=https://github.com/hjmacemail/lmsbridge}"
cat > /usr/share/nginx/html/config.js <<CFG
window.LMSBRIDGE_API = "${API_BASE_URL}";
window.LMSBRIDGE_APP = "${APP_BASE_URL}";
window.LMSBRIDGE_SOURCE = "${SOURCE_URL}";
CFG

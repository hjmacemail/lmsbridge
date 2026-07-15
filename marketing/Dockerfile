FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html initiative.html selfhost.html config.js robots.txt sitemap.xml llms.txt og-image.png favicon.svg /usr/share/nginx/html/
COPY guides/ /usr/share/nginx/html/guides/
COPY docker-entrypoint.sh /docker-entrypoint.d/99-config.sh
RUN chmod +x /docker-entrypoint.d/99-config.sh
EXPOSE 80

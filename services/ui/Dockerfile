# M1 Web UI
FROM nginxinc/nginx-unprivileged:1.29-alpine@sha256:0c79d56aee561a1d81c63f00eee5fb5fe29279560cdc55e91425133104c7fbe6
# Base image ships brotli 1.2.0 (CVE-2026-111497). Remove once the pinned base includes the fix.
USER root
RUN apk add --no-cache --upgrade "brotli-libs>=1.2.1-r0"
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY static/ /usr/share/nginx/html/
USER 101
EXPOSE 8080

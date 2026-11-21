#!/bin/sh
set -eu

if [ "${NGINX_ENVSUBST_TEMPLATE_DIR:-}" = /etc/nginx/lifeconnect-templates ]; then
    domain=${LIFECONNECT_DOMAIN:-}
    case "$domain" in
        ''|*[!a-z0-9.-]*) domain='' ;;
    esac
    if [ "${#domain}" -gt 253 ] ||
        ! printf '%s\n' "$domain" | grep -Eq '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]([a-z0-9-]{0,61}[a-z0-9])?$'; then
        echo "LIFECONNECT_DOMAIN must be a lowercase DNS hostname without a scheme, port or path" >&2
        exit 1
    fi
fi

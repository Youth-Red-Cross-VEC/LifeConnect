# LifeConnect Frontend — Multi-stage Dockerfile
# Stage 1: Build the React/Vite app
FROM node:24-alpine AS builder

WORKDIR /app
RUN apk upgrade --no-cache && npm install --global --ignore-scripts npm@12.2.3

# Copy package files and install deps
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
# VITE_API_URL must be set at build time (passed via --build-arg)
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# reCAPTCHA v3 site key — must be set at build time (passed via --build-arg)
ARG VITE_RECAPTCHA_SITE_KEY
ENV VITE_RECAPTCHA_SITE_KEY=${VITE_RECAPTCHA_SITE_KEY}

COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:stable-alpine AS runtime

# Remove default nginx config
RUN apk upgrade --no-cache && rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx-upstream.conf /etc/nginx/conf.d/00-upstream.conf
COPY nginx-site.conf /etc/nginx/snippets/site.conf
COPY security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY nginx-production.conf.template /etc/nginx/lifeconnect-templates/default.conf.template
COPY --chmod=755 nginx-validate-domain.sh /docker-entrypoint.d/19-validate-domain.sh
RUN sed -i 's/\r$//' /docker-entrypoint.d/19-validate-domain.sh

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8081/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]

# LifeConnect Frontend — Multi-stage Dockerfile
# Stage 1: Build the React/Vite app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install deps
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
# VITE_API_URL must be set at build time (passed via --build-arg)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# reCAPTCHA v3 site key — must be set at build time (passed via --build-arg)
ARG VITE_RECAPTCHA_SITE_KEY
ENV VITE_RECAPTCHA_SITE_KEY=${VITE_RECAPTCHA_SITE_KEY}

COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:stable-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]

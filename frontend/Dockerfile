# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Build the React/Vite app
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# VITE_API_BASE_URL is injected at build time (baked into the bundle)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Serve with nginx
# Cloud Run injects $PORT at runtime (default: 8080).
# We use envsubst to replace ${PORT} in the nginx template at container start.
# ─────────────────────────────────────────────────────────────────────────────
FROM nginx:alpine

# Install gettext for envsubst (usually included in nginx:alpine already,
# but we explicitly ensure it's available)
RUN apk add --no-cache gettext

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config TEMPLATE (uses ${PORT} placeholder)
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Default PORT for local docker-compose runs; Cloud Run overrides this
ENV PORT=8080

EXPOSE 8080

# nginx:alpine's official "20-envsubst-on-templates" feature automatically
# processes templates in /etc/nginx/templates/ → /etc/nginx/conf.d/
# CMD runs nginx normally
CMD ["nginx", "-g", "daemon off;"]

# Static build of the widget SPA (ticket 07 — Docker Compose), served by
# nginx. Multi-stage: the `node` stage only ever produces `dist/`, it never
# ships — the runtime image is nginx + static files only.

# ---- build ----
FROM node:24-alpine AS build
WORKDIR /app

# Installed separately from the rest of the source so this layer is cached
# across rebuilds that only touch application code.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

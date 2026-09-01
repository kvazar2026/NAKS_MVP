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

# Host origins allowed to embed the widget (ticket 05). Vite inlines VITE_*
# variables at build time, so this has to be a build arg rather than a
# runtime env var — changing it requires rebuilding the image. Empty (the
# default) means same-origin only, which is what the bundled demo page at
# /embed-demo.html uses.
ARG VITE_ALLOWED_PARENT_ORIGINS=""
ENV VITE_ALLOWED_PARENT_ORIGINS=$VITE_ALLOWED_PARENT_ORIGINS

RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck is defined once, in docker-compose.yml (not duplicated here —
# a compose-level `healthcheck:` fully replaces any Dockerfile HEALTHCHECK
# for that service, so keeping both would just be two copies to drift).

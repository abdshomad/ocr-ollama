# syntax=docker/dockerfile:1.4
FROM node:22-alpine AS frontend-build

WORKDIR /build
ENV npm_config_cache=/root/.cache/npm

COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN --mount=type=cache,target=/root/.cache/npm \
    npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /build/dist /usr/share/nginx/html

EXPOSE 80

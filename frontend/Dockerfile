# ─────────────────────────────────────────────
#  NyumbaLink Frontend — Multi-stage Dockerfile
# ─────────────────────────────────────────────

# ── Development ───────────────────────────────
FROM node:20-alpine AS development

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

# ── Build ─────────────────────────────────────
FROM node:20-alpine AS builder

ARG REACT_APP_API_URL
ARG REACT_APP_GOOGLE_MAPS_API_KEY

WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .

# Inject build-time env vars
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_GOOGLE_MAPS_API_KEY=$REACT_APP_GOOGLE_MAPS_API_KEY

RUN npm run build

# ── Production — served by Nginx ──────────────
FROM nginx:1.27-alpine AS production

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

COPY docker/nginx/spa.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["nginx", "-g", "daemon off;"]

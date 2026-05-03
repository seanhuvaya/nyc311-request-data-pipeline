# --- Stage 1: build the static bundle ---
FROM node:20-alpine AS builder

WORKDIR /app

# VITE_* vars are baked at build time, not runtime.
# Pass --build-arg VITE_API_URL=https://api.nyc311.seanhuvaya.dev (or override per env).
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Install deps. Use npm ci when a lockfile exists, fall back to npm install otherwise.
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
RUN npm run build

# --- Stage 2: serve via nginx ---
FROM nginx:alpine AS runner

# SPA fallback: any unknown path returns index.html so client-side routing works.
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location ~* \\.(js|css|png|jpg|jpeg|gif|svg|ico|woff2?)$ {\n\
        expires 7d;\n\
        add_header Cache-Control "public, max-age=604800, immutable";\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

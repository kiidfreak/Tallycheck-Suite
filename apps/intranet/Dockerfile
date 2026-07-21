# Multi-stage build for the Angular intranet frontend.
# Build context is the monorepo root so the Nx build can resolve libs/.
#   docker build -f apps/intranet/Dockerfile -t omni-intranet-frontend .

# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app

# Install deps first for better layer caching.
COPY package.json package-lock.json .npmrc ./
RUN npm ci --legacy-peer-deps

# Bring in the rest of the workspace and build the production bundle.
COPY . .
RUN npx nx build intranet --configuration=production

# ---- Serve stage ----
FROM nginx:1.27-alpine
COPY apps/intranet/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/apps/intranet/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

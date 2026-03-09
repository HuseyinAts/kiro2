# Multi-stage build for optimized production image
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (both prod and dev needed for build)
RUN npm ci

# Copy application code
COPY . .

# Build the application (tsc + vite)
# Override production API URL for Docker (nginx proxies /api/ to backend)
ENV VITE_API_URL=""
ENV VITE_WS_URL=""
# Show demo login buttons (Öğrenci/Öğretmen/Veli/Admin) when build arg is set
ARG VITE_SHOW_DEMO=false
ENV VITE_SHOW_DEMO=${VITE_SHOW_DEMO}
RUN npm run build

# Production stage - nginx for static files + API proxy
FROM nginx:alpine AS production

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3   CMD wget -q --spider http://localhost:3000 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

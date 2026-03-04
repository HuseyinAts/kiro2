# Multi-stage build for optimized production image
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (both prod and dev needed for build)
RUN npm ci

# Copy application code
COPY . .

# Build the application (vite only; run tsc separately in CI)
RUN npm run build:fast

# Production stage
FROM node:18-alpine AS production

# Install serve for static file serving
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

# Create a non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Change ownership of the app directory
RUN chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start the application
CMD ["serve", "-s", "dist", "-l", "3000"]
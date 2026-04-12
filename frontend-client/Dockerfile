# Build stage (Using standard node to fix native binding errors)
FROM node:20-slim AS builder

WORKDIR /app

# Only copy package.json (intentionally dropping the lockfile to bypass the npm bug)
COPY package.json ./

# Install dependencies freshly
RUN npm install

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage (Using Alpine here is fine since it just serves static files)
FROM node:20-alpine

WORKDIR /app

# Install serve to run the application
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:5173', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["serve", "-s", "dist", "-l", "5173"]
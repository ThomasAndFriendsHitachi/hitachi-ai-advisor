# Build stage (Using standard node to fix native binding errors)
FROM node:20-slim AS builder

WORKDIR /app

# Only copy package.json (intentionally dropping the lockfile to bypass host OS conflicts)
COPY package.json ./

# Install all dependencies while ignoring optional ones (Prevents Tailwind from hanging)
RUN npm install --omit=optional

# Explicitly install Rollup native Linux binaries (Fixes Vite "Cannot find module" error)
# This ensures Vite finds its engine regardless of the host system architecture
RUN npm install @rollup/rollup-linux-x64-gnu @rollup/rollup-linux-arm64-gnu -O

# Copy the rest of the source code
COPY . .

# Build the application
RUN npm run build

# Production stage (Using Alpine here is fine since it just serves static files)
FROM node:20-alpine

WORKDIR /app

# Install serve to run the application
RUN npm install -g serve

# Copy built application from the builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:5173', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["serve", "-s", "dist", "-l", "5173"]
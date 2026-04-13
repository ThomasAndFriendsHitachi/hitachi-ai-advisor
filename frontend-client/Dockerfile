# Build stage
FROM node:20-slim AS builder

WORKDIR /app

# --- ARGUMENTS INJECTION ---
# These must match the names in your docker-compose 'args' section
ARG VITE_API_URL
ARG VITE_USE_MOCK_DATA
ARG VITE_APP_TITLE

# Set them as ENV variables so 'npm run build' can see them
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_USE_MOCK_DATA=$VITE_USE_MOCK_DATA
ENV VITE_APP_TITLE=$VITE_APP_TITLE

# Copy package.json
COPY package.json ./

# Install dependencies
RUN npm install --omit=optional

# Install Rollup native binaries
RUN npm install @rollup/rollup-linux-x64-gnu @rollup/rollup-linux-arm64-gnu -O

# Copy the rest of the source code
COPY . .

# Build the application (Vite will now bake the ENV vars into the JS files)
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built application
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:5173', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["serve", "-s", "dist", "-l", "5173"]
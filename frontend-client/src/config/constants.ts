/**
 * Application Constants
 * 
 * Centralized configuration for API endpoints, UI constants, and application settings
 */

export const APP_CONFIG = {
  title: import.meta.env.VITE_APP_TITLE || 'Hitachi AI Advisor',
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:3000',
}

/**
 * API Endpoints
 * These endpoints communicate with WebServer #2 (Node.js + Express)
 */
export const API_ENDPOINTS = {
  // TODO: Define endpoints based on backend implementation
  // Example structure:
  // suggestions: {
  //   list: '/suggestions',
  //   get: (id: string) => `/suggestions/${id}`,
  //   approve: (id: string) => `/suggestions/${id}/approve`,
  //   reject: (id: string) => `/suggestions/${id}/reject`,
  // },
}

/**
 * HTTP Status Codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
} as const

/**
 * UI Constants
 */
export const UI_CONFIG = {
  defaultTimeout: 5000,
  maxRetries: 3,
}

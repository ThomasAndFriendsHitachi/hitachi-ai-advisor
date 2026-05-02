/**
 * TypeScript Type Definitions
 * 
 * Centralized type definitions for API responses, UI state, and application data
 */

/**
 * API Response wrapper type
 */
export interface ApiResponse<T> {
  data: T
  status: number
  message?: string
}

/**
 * Error response type
 */
export interface ApiError {
  status: number
  message: string
  details?: Record<string, unknown>
}

/**
 * TODO: Define types for your domain models
 * Example:
 * 
 * export interface Suggestion {
 *   id: string
 *   title: string
 *   description: string
 *   status: 'pending' | 'approved' | 'rejected'
 *   createdAt: string
 *   updatedAt: string
 * }
 * 
 * export interface Manager {
 *   id: string
 *   username: string
 *   email: string
 *   role: string
 * }
 */

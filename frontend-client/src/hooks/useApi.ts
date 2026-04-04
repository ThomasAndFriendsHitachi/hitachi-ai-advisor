/**
 * Custom Hook for API Calls
 * 
 * Provides a reusable hook for making API requests with loading and error handling
 */

import { useState, useCallback } from 'react'
import apiClient from '../config/api'
import { ApiError } from '../types'

export interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
}

/**
 * Hook for handling API calls with state management
 * 
 * @template T - The expected response data type
 * @returns Object containing data, loading state, error, and refetch function
 * 
 * @example
 * const { data, loading, error, refetch } = useApi<Suggestion[]>('/api/suggestions')
 */
export function useApi<T>(
  url: string,
  options?: { skip?: boolean }
): UseApiState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: !options?.skip,
    error: null,
  })

  const refetch = useCallback(async () => {
    setState({ data: null, loading: true, error: null })
    try {
      const response = await apiClient.get<T>(url)
      setState({ data: response.data, loading: false, error: null })
    } catch (error) {
      const apiError: ApiError = {
        status: 0,
        message: 'An error occurred',
      }
      setState({ data: null, loading: false, error: apiError })
    }
  }, [url])

  // Initial fetch if not skipped
  if (!options?.skip) {
    // TODO: Implement effect to fetch data on mount
  }

  return { ...state, refetch }
}

import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { Dashboard } from '@/pages/Dashboard'
import { CaseDetails } from './pages/CaseDetails'
import { ReviewSuggestions } from './pages/ReviewSuggestions'
import { Analytics } from './pages/Analytics'
import { ProjectHistory } from './pages/ProjectHistory'
import { Settings } from './pages/Settings'
import './App.css'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Root Route Handler - Redirects to appropriate page
function RootRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    console.log('[App] Route - isLoading:', isLoading, 'isAuthenticated:', isAuthenticated)
  }, [isLoading, isAuthenticated])

  return (
    <Routes>
      {/* Root path - redirects to login or dashboard based on auth */}
      <Route path="/" element={<RootRoute />} />

      {/* Login page - only accessible when not authenticated */}
      <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" replace />} />

      {/* Dashboard - protected route */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* CaseDetails - protected route */}
      <Route
        path="/cases/:id"
        element={
          <ProtectedRoute>
            <CaseDetails />
          </ProtectedRoute>
        }
      />

      {/* ReviewSuggestions - protected route */}
      <Route
        path="/review"
        element={
          <ProtectedRoute>
            <ReviewSuggestions />
          </ProtectedRoute>
        }
      />

      {/* Analytics - protected route */}
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        }
      />

      {/* ProjectHistory - protected route */}
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <ProjectHistory />
          </ProtectedRoute>
        }
      />

      {/* Settings - protected route */}
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />
      
      {/* Catch-all - redirect to root */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App

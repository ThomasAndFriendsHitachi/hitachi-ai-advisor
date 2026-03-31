import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // TODO: Initialize app state, fetch initial data from API
    setIsLoading(false)
  }, [])

  if (isLoading) {
    return <div className="app">Loading...</div>
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Hitachi AI Advisor</h1>
        <p>Manager Dashboard</p>
      </header>
      <main className="app-main">
        <section className="intro">
          <h2>Welcome to the AI Advisor Dashboard</h2>
          <p>
            This dashboard allows Hitachi managers to review, approve, and manage AI-generated suggestions.
          </p>
          <div className="feature-list">
            <div className="feature-item">
              <h3>📋 Review Suggestions</h3>
              <p>View all AI-generated suggestions and their details</p>
            </div>
            <div className="feature-item">
              <h3>✅ Approve Changes</h3>
              <p>Approve or reject AI recommendations</p>
            </div>
            <div className="feature-item">
              <h3>📊 Analytics</h3>
              <p>Track approval rates and trends</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App

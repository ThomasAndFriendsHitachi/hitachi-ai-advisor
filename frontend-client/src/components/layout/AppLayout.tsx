import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, Moon, Sun, BookOpen, AlertCircle, BarChart3, History, Settings, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import { Toaster } from "@/components/ui/sonner"

const NAVIGATION = [
  { label: 'Decision Journal', href: '/decision-journal', icon: FileText },
  { label: 'Review Suggestions', href: '/review', icon: AlertCircle },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'Project History', href: '/history', icon: History },
  { label: 'Settings', href: '/settings', icon: Settings },
]

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { isDarkMode, toggleDarkMode } = useTheme()
  const { logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false) // Closed by default
  const location = useLocation()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - using relative & flex to fix the stuck button bug */}
      <aside 
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } border-r border-border bg-background transition-all duration-300 overflow-hidden relative flex flex-col shrink-0`}
      >
        {/* Sidebar Header */}
        <div className="border-b border-border px-4 py-4 shrink-0 w-64">
          <Link to="/dashboard" className="flex items-center gap-2 whitespace-nowrap">
            <div className="w-8 h-8 bg-hitachi-blue rounded-md flex items-center justify-center">
              <span className="text-white text-sm font-bold">H</span>
            </div>
            <h1 className="text-lg font-bold text-foreground">Hitachi AI</h1>
          </Link>
        </div>

        {/* Sidebar Nav */}
        <nav className="p-4 space-y-2 flex-1 overflow-y-auto w-64">
          {NAVIGATION.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm whitespace-nowrap ${
                  isActive 
                    ? 'bg-hitachi-blue text-white' 
                    : 'text-foreground hover:bg-hitachi-blue hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Sidebar Footer - mt-auto keeps it at bottom without escaping overflow */}
        <div className="border-t border-border p-4 mt-auto w-64 bg-background">
          <Button variant="outline" className="w-full text-sm whitespace-nowrap">
            <BookOpen className="w-4 h-4 mr-2 shrink-0" />
            Documentation
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-40 border-b border-border bg-background shrink-0">
          <div className="flex items-center justify-between h-16 px-6 gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-md border border-border hover:bg-muted transition-colors"
            >
              <Menu className="w-4 h-4 text-muted-foreground shrink-0" />
            </button>

            {/* Right Controls */}
            <div className="flex items-center gap-4">
              <button onClick={toggleDarkMode} className="p-2 rounded-md border border-border hover:bg-muted transition-colors">
                {isDarkMode ? <Sun className="w-4 h-4 text-muted-foreground" /> : <Moon className="w-4 h-4 text-muted-foreground" />}
              </button>
              <Separator orientation="vertical" className="h-6" />
              <Button variant="ghost" size="sm" onClick={handleLogout} className="text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors">
                Logout
              </Button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-hidden relative">
          {children}
        </div>
      </div>
      <Toaster position="bottom-right" richColors />
    </div>
  )
}
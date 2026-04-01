import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Moon, Sun, Eye, EyeOff, LogOut, AlertCircle, Clock, CheckCircle, BarChart3, History, Settings, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

// Mock data for release cases
const MOCK_CASES = [
  {
    id: '1',
    project: 'Q1 2026 Release Bundle',
    riskScore: 'High',
    status: 'Pending Approval',
    date: '2026-04-01',
  },
  {
    id: '2',
    project: 'Infrastructure Migration',
    riskScore: 'Medium',
    status: 'Under Review',
    date: '2026-03-31',
  },
  {
    id: '3',
    project: 'Security Patch Deploy',
    riskScore: 'High',
    status: 'Pending Approval',
    date: '2026-03-30',
  },
  {
    id: '4',
    project: 'Database Optimization',
    riskScore: 'Low',
    status: 'Approved',
    date: '2026-03-28',
  },
  {
    id: '5',
    project: 'API Rate Limiting Update',
    riskScore: 'Medium',
    status: 'Pending Approval',
    date: '2026-03-27',
  },
]

const NAVIGATION = [
  { label: 'Review Suggestions', href: '#review', icon: AlertCircle },
  { label: 'Analytics', href: '#analytics', icon: BarChart3 },
  { label: 'Project History', href: '#history', icon: History },
  { label: 'Settings', href: '#settings', icon: Settings },
]

export function Dashboard() {
  const navigate = useNavigate()
  const { isDarkMode, toggleDarkMode } = useTheme()
  const { logout } = useAuth()
  const [isPrivacyMode, setIsPrivacyMode] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  console.log('[Dashboard] Rendering - isDarkMode:', isDarkMode, 'isPrivacyMode:', isPrivacyMode)

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High':
        return 'text-red-600 bg-red-50'
      case 'Medium':
        return 'text-amber-600 bg-amber-50'
      case 'Low':
        return 'text-green-600 bg-green-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'High':
        return <AlertCircle className="w-4 h-4 mr-1" />
      case 'Medium':
        return <Clock className="w-4 h-4 mr-1" />
      case 'Low':
        return <CheckCircle className="w-4 h-4 mr-1" />
      default:
        return null
    }
  }

  const maskProjectName = (name: string) => {
    if (!isPrivacyMode) return name
    return '█'.repeat(Math.min(name.length, 20))
  }

  const handleCaseClick = (caseId: string) => {
    console.log('[Dashboard] Navigating to case:', caseId)
    // TODO: Navigate to /cases/[id]
  }

  const handleLogout = () => {
    console.log('[Dashboard] Logout initiated')
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside 
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } border-r border-border bg-background transition-all duration-300 overflow-hidden`}
      >
        {/* Sidebar Header */}
        <div className="border-b border-border px-4 py-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-hitachi-blue rounded-md flex items-center justify-center">
              <span className="text-white text-sm font-bold">H</span>
            </div>
            <h1 className="text-lg font-bold text-foreground">Hitachi AI</h1>
          </div>
        </div>

        {/* Sidebar Nav */}
        <nav className="p-4 space-y-2">
          {NAVIGATION.map((item) => {
            const Icon = item.icon
            return (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-hitachi-blue hover:text-white transition-colors text-sm text-foreground"
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </a>
            )
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="border-t border-border p-4 absolute bottom-0 w-64">
          <Button variant="outline" className="w-full text-sm">
            <BookOpen className="w-4 h-4 mr-2" />
            Documentation
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-40 border-b border-border bg-background">
          <div className="flex items-center justify-between h-16 px-6 gap-4">
            {/* Left: Menu trigger & title */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-md border border-border hover:bg-muted transition-colors"
                title="Toggle sidebar"
              >
                <Menu className="w-4 h-4 text-muted-foreground" />
              </button>
              <h2 className="text-lg font-semibold text-foreground">
                Release Cases Inbox
              </h2>
            </div>

            {/* Right: Controls */}
            <div className="flex items-center gap-4">
              {/* Privacy Toggle */}
              <div 
                className="flex items-center gap-2 px-3 py-1 rounded-md border border-border hover:bg-muted transition-colors cursor-pointer"
                onClick={() => setIsPrivacyMode(!isPrivacyMode)}
                title={isPrivacyMode ? 'Disable privacy mode' : 'Enable privacy mode'}
              >
                {isPrivacyMode ? (
                  <EyeOff className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <Eye className="w-4 h-4 text-muted-foreground" />
                )}
              </div>

              <Separator orientation="vertical" className="h-6" />

              {/* Dark Mode Toggle */}
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-md border border-border hover:bg-muted transition-colors"
                title={isDarkMode ? 'Toggle light mode' : 'Toggle dark mode'}
              >
                {isDarkMode ? (
                  <Sun className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <Moon className="w-4 h-4 text-muted-foreground" />
                )}
              </button>

              {/* Logout Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleLogout}>
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <Card className="bg-card">
            {/* Table Header */}
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-sm font-semibold text-card-foreground">
                Pending & Recent Approvals ({MOCK_CASES.length} items)
              </h3>
            </div>

            {/* Inbox Table */}
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-b border-border hover:bg-transparent">
                    <TableHead className="font-semibold text-card-foreground">
                      Project Name
                    </TableHead>
                    <TableHead className="font-semibold text-card-foreground">
                      Risk Score
                    </TableHead>
                    <TableHead className="font-semibold text-card-foreground">
                      Status
                    </TableHead>
                    <TableHead className="text-right font-semibold text-card-foreground">
                      Date
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {MOCK_CASES.map((caseItem) => (
                    <TableRow
                      key={caseItem.id}
                      onClick={() => handleCaseClick(caseItem.id)}
                      className="cursor-pointer hover:bg-muted transition-colors border-b border-border"
                    >
                      <TableCell className="font-medium text-card-foreground">
                        <span
                          className={
                            isPrivacyMode ? 'blur-sm select-none' : ''
                          }
                        >
                          {maskProjectName(caseItem.project)}
                        </span>
                      </TableCell>

                      <TableCell>
                        <div
                          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${getRiskColor(
                            caseItem.riskScore
                          )}`}
                        >
                          {getRiskIcon(caseItem.riskScore)}
                          {caseItem.riskScore}
                        </div>
                      </TableCell>

                      <TableCell>
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          {caseItem.status}
                        </span>
                      </TableCell>

                      <TableCell className="text-right text-sm text-muted-foreground">
                        {new Date(caseItem.date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Empty State Footer */}
            <div className="px-6 py-4 border-t border-border bg-muted/30 text-sm text-muted-foreground text-center">
              Click on any case to view details and approve/reject recommendations
            </div>
          </Card>
        </main>
      </div>
    </div>
  )
}

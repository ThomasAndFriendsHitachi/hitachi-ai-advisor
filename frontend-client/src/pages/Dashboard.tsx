import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { io, Socket } from 'socket.io-client'
import { Eye, EyeOff, AlertCircle, Clock, CheckCircle, Activity } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AppLayout } from '@/components/layout/AppLayout'
import { toast } from 'sonner'

// Mock data for release cases
const MOCK_CASES = [
  { id: '1', project: 'Q1 2026 Release Bundle', riskScore: 'High', status: 'Pending Approval', date: '2026-04-01' },
  { id: '2', project: 'Infrastructure Migration', riskScore: 'Medium', status: 'Under Review', date: '2026-03-31' },
  { id: '3', project: 'Security Patch Deploy', riskScore: 'High', status: 'Pending Approval', date: '2026-03-30' },
  { id: '4', project: 'Database Optimization', riskScore: 'Low', status: 'Approved', date: '2026-03-28' },
  { id: '5', project: 'API Rate Limiting Update', riskScore: 'Medium', status: 'Pending Approval', date: '2026-03-27' },
]

export function Dashboard() {
  const navigate = useNavigate()
  const [isPrivacyMode, setIsPrivacyMode] = useState(false)
  const [cases, setCases] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLive, setIsLive] = useState(false)

  // Wrapped in useCallback so we can safely use it inside the socket listener
  const fetchCases = useCallback(async (isSilentUpdate = false) => {
    const useMock = import.meta.env.VITE_USE_MOCK_DATA === 'true'
    
    if (useMock) {
      setCases(MOCK_CASES)
      setIsLoading(false)
      return
    }

    try {
      // Only show the hard loading state if it's the initial fetch
      if (!isSilentUpdate) setIsLoading(true)
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/cases`)
      const dbCases = await response.json()
      
      // Map PostgreSQL ai_tasks_results to frontend table structure
      const formattedCases = dbCases.map((dbCase: any) => ({
        id: dbCase.id,
        project: dbCase.raw_payload?.repository?.name || 'GitHub Webhook Event',
        riskScore: 'Medium', // We will calculate this later based on AI agent output
        status: dbCase.status === 'received' ? 'Pending Review' : dbCase.status,
        date: dbCase.processed_at
      }))
      
      setCases(formattedCases)
    } catch (error) {
      console.error("Failed to fetch real cases, falling back to mock data:", error)
      setCases(MOCK_CASES) // Fallback if backend is down
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // 1. Fetch initial data
    fetchCases()

    // 2. Connect to WebSocket Server (WebServer #2)
    const socketUrl = import.meta.env.VITE_API_URL || 'http://localhost:3001'
    const socket: Socket = io(socketUrl)

    socket.on('connect', () => setIsLive(true))
    socket.on('disconnect', () => setIsLive(false))

    // 3. Listen for AI Agent completing a task via Redis Pub/Sub
    socket.on('task_updated', (data) => {
      // Refresh the table quietly (no hard loading screen)
      fetchCases(true)
      
      // Pop a Sonner toast notification
      toast.info("New AI Analysis Complete", {
        description: `Task ${String(data.db_id).slice(0,8)}... has been processed and added to your inbox.`,
      })
    })

    return () => {
      socket.disconnect()
    }
  }, [fetchCases])

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High': return 'text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400'
      case 'Medium': return 'text-amber-600 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-400'
      case 'Low': return 'text-green-600 bg-green-50 dark:bg-green-900/30 dark:text-green-400'
      default: return 'text-gray-600 bg-gray-50 dark:bg-gray-800 dark:text-gray-300'
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'High': return <AlertCircle className="w-4 h-4 mr-1" />
      case 'Medium': return <Clock className="w-4 h-4 mr-1" />
      case 'Low': return <CheckCircle className="w-4 h-4 mr-1" />
      default: return null
    }
  }

  const maskProjectName = (name: string) => {
    if (!isPrivacyMode) return name
    return '█'.repeat(Math.min(name.length, 20))
  }

  const handleCaseClick = (caseId: string) => {
    console.log('[Dashboard] Navigating to case:', caseId)
    navigate(`/cases/${caseId}`)
  }

  return (
    <AppLayout>
      <div className="h-full overflow-y-auto bg-background p-6">
        
        {/* Table Controls (Title & Privacy Toggle) */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-foreground">Release Cases Inbox</h2>
            
            {/* Live Connection Badge */}
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${isLive ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50' : 'bg-muted text-muted-foreground border-border'}`}>
              <Activity className={`w-3 h-3 ${isLive ? 'animate-pulse' : ''}`} />
              {isLive ? 'Live Sync' : 'Offline'}
            </div>
          </div>

          <div 
            className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-muted transition-colors cursor-pointer"
            onClick={() => setIsPrivacyMode(!isPrivacyMode)}
            title={isPrivacyMode ? 'Disable privacy mode' : 'Enable privacy mode'}
          >
            {isPrivacyMode ? <EyeOff className="w-4 h-4 text-muted-foreground" /> : <Eye className="w-4 h-4 text-muted-foreground" />}
            <span className="text-sm font-medium text-muted-foreground">Privacy Mode</span>
          </div>
        </div>

        <Card>
          {/* Table Header */}
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-sm font-semibold text-card-foreground">
              Pending & Recent Approvals ({cases.length} items)
            </h3>
          </div>

          {/* Inbox Table */}
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b border-border hover:bg-transparent">
                  <TableHead className="font-semibold text-card-foreground">Project Name</TableHead>
                  <TableHead className="font-semibold text-card-foreground">Risk Score</TableHead>
                  <TableHead className="font-semibold text-card-foreground">Status</TableHead>
                  <TableHead className="text-right font-semibold text-card-foreground">Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-8 text-muted-foreground">Loading cases...</TableCell></TableRow>
                ) : cases.length === 0 ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-8 text-muted-foreground">No cases found in database. Waiting for webhooks...</TableCell></TableRow>
                ) : (
                  cases.map((caseItem) => (
                    <TableRow 
                      key={caseItem.id} 
                      onClick={() => handleCaseClick(caseItem.id)} 
                      className="cursor-pointer hover:bg-muted transition-colors border-b border-border"
                    >
                      <TableCell className="font-medium text-card-foreground">
                        <span className={isPrivacyMode ? 'blur-sm select-none' : ''}>
                          {maskProjectName(caseItem.project)}
                        </span>
                      </TableCell>

                      <TableCell>
                        <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${getRiskColor(caseItem.riskScore)}`}>
                          {getRiskIcon(caseItem.riskScore)}
                          {caseItem.riskScore}
                        </div>
                      </TableCell>

                      <TableCell>
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${caseItem.status === 'Pending Review' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-primary/10 text-primary'}`}>
                          {caseItem.status}
                        </span>
                      </TableCell>

                      <TableCell className="text-right text-sm text-muted-foreground">
                        {new Date(caseItem.date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Empty State Footer */}
          <div className="px-6 py-4 border-t border-border bg-muted/30 text-sm text-muted-foreground text-center">
            Click on any case to view details and approve/reject recommendations
          </div>
        </Card>
      </div>
    </AppLayout>
  )
}
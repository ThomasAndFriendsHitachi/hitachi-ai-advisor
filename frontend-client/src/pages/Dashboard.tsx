import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, AlertCircle, Clock, CheckCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AppLayout } from '@/components/layout/AppLayout'

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

  useEffect(() => {
    const fetchCases = async () => {
      const useMock = import.meta.env.VITE_USE_MOCK_DATA === 'true'
      
      if (useMock) {
        setCases(MOCK_CASES)
        setIsLoading(false)
      } else {
        try {
          const response = await fetch(`${import.meta.env.VITE_API_URL}/api/cases`)
          const dbCases = await response.json()
          
          // Map PostgreSQL ai_tasks_results to frontend table structure
          const formattedCases = dbCases.map((dbCase: any) => ({
            id: dbCase.id,
            project: dbCase.raw_payload?.repository?.name || 'GitHub Webhook Event',
            riskScore: 'Medium', // We will calculate this later based on AI agent output
            status: dbCase.status,
            date: dbCase.processed_at
          }))
          
          setCases(formattedCases)
        } catch (error) {
          console.error("Failed to fetch real cases, falling back to mock data:", error)
          setCases(MOCK_CASES) // Fallback if backend is down
        } finally {
          setIsLoading(false)
        }
      }
    }

    fetchCases()
  }, [])

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High': return 'text-red-600 bg-red-50'
      case 'Medium': return 'text-amber-600 bg-amber-50'
      case 'Low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
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
          <h2 className="text-2xl font-bold text-foreground">Release Cases Inbox</h2>
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
                  <TableRow><TableCell colSpan={4} className="text-center py-4">Loading cases...</TableCell></TableRow>
                ) : cases.length === 0 ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-4 text-muted-foreground">No cases found in database.</TableCell></TableRow>
                ) : (
                  cases.map((caseItem) => (
                    <TableRow key={caseItem.id} onClick={() => handleCaseClick(caseItem.id)} className="cursor-pointer hover:bg-muted">
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
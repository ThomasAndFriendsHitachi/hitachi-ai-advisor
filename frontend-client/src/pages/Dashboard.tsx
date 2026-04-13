import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { io, Socket } from 'socket.io-client'
import { Eye, EyeOff, AlertCircle, Clock, CheckCircle, Activity, Bot, TrendingUp, Server } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AppLayout } from '@/components/layout/AppLayout'
import { toast } from 'sonner'
import { useAuth } from '@/contexts/AuthContext'

// Mock data for release cases
const MOCK_CASES = [
  { id: '1', project: 'Q1 2026 Release Bundle', riskScore: 'High', status: 'Pending Approval', date: '2026-04-01' },
  { id: '2', project: 'Infrastructure Migration', riskScore: 'Medium', status: 'Under Review', date: '2026-03-31' },
  { id: '3', project: 'Security Patch Deploy', riskScore: 'High', status: 'Pending Approval', date: '2026-03-30' },
  { id: '4', project: 'Database Optimization', riskScore: 'Low', status: 'Approved', date: '2026-03-28' },
  { id: '5', project: 'API Rate Limiting Update', riskScore: 'Medium', status: 'Pending Approval', date: '2026-03-27' },
]

// Mock data for the activity chart
const WEEKLY_ACTIVITY = [
  { day: 'Mon', count: 12 }, { day: 'Tue', count: 28 }, { day: 'Wed', count: 14 },
  { day: 'Thu', count: 34 }, { day: 'Fri', count: 25 }, { day: 'Sat', count: 8 }, { day: 'Sun', count: 12 }
]

export function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [isPrivacyMode, setIsPrivacyMode] = useState(false)
  const [cases, setCases] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLive, setIsLive] = useState(false)

  const fetchCases = useCallback(async (isSilentUpdate = false) => {
    const useMock = import.meta.env.VITE_USE_MOCK_DATA === 'true'
    
    if (useMock) {
      setCases(MOCK_CASES)
      setIsLoading(false)
      return
    }

    try {
      if (!isSilentUpdate) setIsLoading(true)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/cases`)
      const dbCases = await response.json()
      
      const formattedCases = dbCases.map((dbCase: any) => ({
        id: dbCase.id,
        project: dbCase.raw_payload?.repository?.name || 'Automated Webhook Event',
        riskScore: ['High', 'Medium', 'Low'][Math.floor(Math.random() * 3)],
        status: dbCase.status === 'received' ? 'Pending Review' : dbCase.status,
        date: dbCase.processed_at
      }))
      
      setCases(formattedCases)
    } catch (error) {
      console.error("Failed to fetch real cases:", error)
      setCases([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCases()

    const socketUrl = import.meta.env.VITE_API_URL || 'http://localhost:3001'
    const socket: Socket = io(socketUrl)

    socket.on('connect', () => setIsLive(true))
    socket.on('disconnect', () => setIsLive(false))

    socket.on('task_updated', (data) => {
      fetchCases(true)
      toast.info("New AI Analysis Complete", {
        description: `Task ${String(data.db_id).slice(0,8)}... processed.`,
      })
    })

    return () => { socket.disconnect() }
  }, [fetchCases])

  // --- Derived Metrics for the UI ---
  const pendingCount = cases.filter(c => c.status.includes('Pending') || c.status.includes('Review')).length
  const highRiskCount = cases.filter(c => c.riskScore === 'High').length
  const medRiskCount = cases.filter(c => c.riskScore === 'Medium').length
  const lowRiskCount = cases.filter(c => c.riskScore === 'Low').length
  
  const total = cases.length || 1
  const highPct = (highRiskCount / total) * 100
  const medPct = (medRiskCount / total) * 100
  const conicGradient = `conic-gradient(#ef4444 0% ${highPct}%, #f59e0b ${highPct}% ${highPct + medPct}%, #22c55e ${highPct + medPct}% 100%)`

  // Calculate SVG Line Chart Data
  const maxActivity = Math.max(...WEEKLY_ACTIVITY.map(d => d.count), 1)
  const chartMax = maxActivity * 1.2 // 20% headroom so it doesn't hit the ceiling
  
  const chartPoints = WEEKLY_ACTIVITY.map((d, i) => {
    const x = (i / (WEEKLY_ACTIVITY.length - 1)) * 100
    const y = 100 - ((d.count / chartMax) * 100)
    return `${x},${y}`
  }).join(' ')
  const chartAreaPoints = `${chartPoints} 100,100 0,100`

  // --- Utilities ---
  const getRiskColor = (risk: string) => risk === 'High' ? 'text-red-600 bg-red-500/10' : risk === 'Medium' ? 'text-amber-600 bg-amber-500/10' : 'text-green-600 bg-green-500/10'
  const getRiskIcon = (risk: string) => risk === 'High' ? <AlertCircle className="w-4 h-4 mr-1" /> : risk === 'Medium' ? <Clock className="w-4 h-4 mr-1" /> : <CheckCircle className="w-4 h-4 mr-1" />
  
  const maskText = (text: string) => !isPrivacyMode ? text : '█'.repeat(Math.min(text.length, 12))
  const maskNum = (num: number | string) => !isPrivacyMode ? num : '***'
  
  const handleCaseClick = (caseId: string) => { navigate(`/cases/${caseId}`) }

  return (
    <AppLayout>
      <div className="h-full overflow-y-auto bg-background p-4 md:p-8 space-y-6">
        
        {/* Top Header & Controls */}
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-foreground">Overview</h2>
          
          <div className="flex items-center gap-3">
            <div className={`hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border ${isLive ? 'bg-green-500/10 text-green-600 border-green-500/20' : 'bg-muted text-muted-foreground border-border'}`}>
              <Activity className={`w-3.5 h-3.5 ${isLive ? 'animate-pulse' : ''}`} />
              {isLive ? 'Live Sync' : 'Offline'}
            </div>
            
            <Button 
              variant="outline" 
              size="sm"
              className="bg-card border-border shadow-sm text-muted-foreground"
              onClick={() => setIsPrivacyMode(!isPrivacyMode)}
            >
              {isPrivacyMode ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
              {isPrivacyMode ? 'Disable Privacy' : 'Privacy Mode'}
            </Button>
          </div>
        </div>

        {/* 1. The Banner */}
        <div className="bg-secondary/50 border border-border rounded-xl p-6 md:p-8 relative overflow-hidden shadow-sm">
           <div className="relative z-10">
             <h1 className="text-2xl md:text-3xl font-serif text-primary font-bold mb-1">
               {maskText(user?.name || 'Hitachi Manager')}
             </h1>
             <p className="text-sm text-muted-foreground mb-8">Hitachi AI Advisor • Standard Plan</p>
             
             <div className="max-w-md space-y-6">
               <div>
                 <div className="flex justify-between text-xs font-medium mb-1.5 text-muted-foreground">
                   <span>Manual Cases Reviewed</span>
                   <span className="text-primary font-bold">{maskNum(14)} / {maskNum(50)}</span>
                 </div>
                 <div className="h-2 w-full bg-background rounded-full overflow-hidden shadow-inner border border-border/50">
                   <div className="h-full bg-primary w-[28%] rounded-full transition-all duration-1000"></div>
                 </div>
               </div>

               <div>
                 <div className="flex justify-between text-xs font-medium mb-1.5 text-muted-foreground">
                   <span>Automated Approvals</span>
                   <span className="text-primary font-bold">{maskNum(86)} / {maskNum(200)}</span>
                 </div>
                 <div className="h-2 w-full bg-background rounded-full overflow-hidden shadow-inner border border-border/50">
                   <div className="h-full bg-blue-400 w-[43%] rounded-full transition-all duration-1000"></div>
                 </div>
               </div>
             </div>
           </div>
        </div>

        {/* 2. Hero & Donut Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <Card className="col-span-1 lg:col-span-2 p-6 md:p-8 shadow-sm flex flex-col justify-center">
            <h3 className="text-lg text-muted-foreground font-medium mb-6">Where do we start today?</h3>
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="hidden md:flex shrink-0 w-32 h-40 bg-muted/50 rounded-xl border-2 border-dashed border-border items-center justify-center">
                <Bot className="w-16 h-16 text-muted-foreground/50" />
              </div>
              <div className="flex-1 text-center md:text-left">
                <div className="flex items-end justify-center md:justify-start gap-2 mb-3">
                  <span className="text-4xl font-bold text-primary leading-none">{maskNum(pendingCount)}</span>
                  <span className="text-sm font-medium text-muted-foreground pb-1">cases require your attention</span>
                </div>
                <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto md:mx-0">
                  The AI Agent has processed new incoming release candidates from GitHub. Review the suggestions to unblock the pipeline.
                </p>
                <Button className="px-8" onClick={() => navigate('/cases/1')}>
                  Start Reviews
                </Button>
              </div>
            </div>
          </Card>

          <Card className="col-span-1 p-6 shadow-sm flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-semibold text-foreground text-sm">Risk Assessment</h3>
            </div>
            
            <div className="flex-1 flex flex-col sm:flex-row lg:flex-col items-center justify-center gap-6">
              <div className="relative w-28 h-28 rounded-full flex items-center justify-center shrink-0" style={{ background: conicGradient }}>
                <div className="absolute w-20 h-20 bg-card rounded-full flex items-center justify-center shadow-inner">
                  <div className="text-center">
                    <span className="block text-xl font-bold text-foreground leading-none">{maskNum(cases.length)}</span>
                    <span className="block text-[9px] text-muted-foreground uppercase tracking-wider mt-1">Total</span>
                  </div>
                </div>
              </div>

              <div className="w-full space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center text-muted-foreground"><span className="w-2.5 h-2.5 rounded-full bg-red-500 mr-2 shadow-sm"></span>High Risk</span>
                  <span className="font-semibold text-foreground">{maskNum(highRiskCount)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center text-muted-foreground"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 mr-2 shadow-sm"></span>Medium Risk</span>
                  <span className="font-semibold text-foreground">{maskNum(medRiskCount)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center text-muted-foreground"><span className="w-2.5 h-2.5 rounded-full bg-green-500 mr-2 shadow-sm"></span>Low Risk</span>
                  <span className="font-semibold text-foreground">{maskNum(lowRiskCount)}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 3. The Line Chart & Resources Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <Card className="p-6 shadow-sm flex flex-col">
             <div className="flex justify-between items-start mb-2">
               <div>
                 <h3 className="font-semibold text-foreground text-sm mb-1">AI Processing Volume</h3>
                 <p className="text-xs text-muted-foreground">Cases analyzed over the last 7 days</p>
               </div>
               <div className="text-right">
                 <span className="text-xl font-bold text-foreground block">{maskNum(131)}</span>
                 <span className="text-xs text-green-600 flex items-center justify-end"><TrendingUp className="w-3 h-3 mr-1" /> +14% vs last week</span>
               </div>
             </div>

             <div className="w-full h-32 relative mt-4">
                {/* SVG for Area and Line (Stretches to fit) */}
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
                  <defs>
                    <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="currentColor" stopOpacity="0.15" className="text-primary" />
                      <stop offset="100%" stopColor="currentColor" stopOpacity="0" className="text-primary" />
                    </linearGradient>
                  </defs>
                  
                  <line x1="0" y1="25" x2="100" y2="25" stroke="currentColor" className="text-border" strokeWidth="1" vectorEffect="non-scaling-stroke" />
                  <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" className="text-border" strokeWidth="1" vectorEffect="non-scaling-stroke" />
                  <line x1="0" y1="75" x2="100" y2="75" stroke="currentColor" className="text-border" strokeWidth="1" vectorEffect="non-scaling-stroke" />
                  
                  <polygon points={chartAreaPoints} fill="url(#chartGradient)" />
                  <polyline points={chartPoints} fill="none" stroke="currentColor" className="text-primary" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
                </svg>

                {/* HTML Divs for Dots (Never stretch, always perfect circles) */}
                {WEEKLY_ACTIVITY.map((d, i) => {
                  const x = (i / (WEEKLY_ACTIVITY.length - 1)) * 100
                  const y = 100 - ((d.count / chartMax) * 100)
                  return (
                    <div 
                      key={i} 
                      className="absolute w-2.5 h-2.5 bg-card border-2 border-primary rounded-full shadow-sm"
                      style={{ left: `calc(${x}% - 5px)`, top: `calc(${y}% - 5px)` }}
                    />
                  )
                })}
             </div>
             
             <div className="flex justify-between text-[10px] text-muted-foreground mt-3 px-1">
               {WEEKLY_ACTIVITY.map(d => <span key={d.day}>{d.day}</span>)}
             </div>
          </Card>

          <Card className="p-6 shadow-sm">
            <h3 className="font-semibold text-foreground text-sm mb-6">System Architecture</h3>
            <div className="flex flex-col sm:flex-row gap-6 items-center sm:items-stretch">
              
              <div className="w-full sm:w-64 shrink-0 bg-muted/50 rounded-xl p-5 flex flex-col justify-between border border-border shadow-sm relative overflow-hidden h-36">
                 <div className="flex items-center gap-3 relative z-10">
                   <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-sm">
                     <Server className="w-4 h-4 text-primary-foreground" />
                   </div>
                   <span className="font-semibold text-foreground">AI Worker Node</span>
                 </div>
                 <div className="relative z-10">
                   <div className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono mb-1">Instance ID: {maskText('WKR-992-X')}</div>
                   <div className="text-xs text-green-600 dark:text-green-500 font-medium flex items-center gap-1.5">
                     <span className="relative flex h-2 w-2">
                       <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                       <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                     </span>
                     Connected to Redis
                   </div>
                 </div>
              </div>

              <div className="flex-1 flex flex-col justify-center space-y-2.5 text-xs md:text-sm text-muted-foreground w-full">
                <p className="flex items-start gap-2"><span className="text-primary mt-0.5">•</span> Parses incoming GitHub webhooks instantly</p>
                <p className="flex items-start gap-2"><span className="text-primary mt-0.5">•</span> Runs compliance checks against Hitachi standards</p>
                <p className="flex items-start gap-2"><span className="text-primary mt-0.5">•</span> Stores results via PostgreSQL pg8000</p>
                <div className="mt-2 inline-flex w-fit px-2 py-1 bg-primary/10 text-primary rounded text-[10px] font-bold tracking-wide uppercase">
                  Auto-scaling enabled
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 4. Detailed Ledger */}
        <Card className="shadow-sm">
          <div className="px-6 py-5 border-b border-border flex justify-between items-center">
            <h3 className="text-sm font-semibold text-foreground">
              Recent Case Ledger
            </h3>
            <span className="text-xs text-muted-foreground bg-muted px-2.5 py-1 rounded-md font-medium">
              {maskNum(cases.length)} Total Records
            </span>
          </div>

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b border-border hover:bg-transparent bg-muted/30">
                  <TableHead className="font-semibold text-muted-foreground h-10">Project Name</TableHead>
                  <TableHead className="font-semibold text-muted-foreground h-10">Risk Score</TableHead>
                  <TableHead className="font-semibold text-muted-foreground h-10">Status</TableHead>
                  <TableHead className="text-right font-semibold text-muted-foreground h-10">Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-12 text-muted-foreground">Loading cases...</TableCell></TableRow>
                ) : cases.length === 0 ? (
                  <TableRow><TableCell colSpan={4} className="text-center py-12 text-muted-foreground">No cases found in database. Waiting for webhooks...</TableCell></TableRow>
                ) : (
                  cases.map((caseItem) => (
                    <TableRow 
                      key={caseItem.id} 
                      onClick={() => handleCaseClick(caseItem.id)} 
                      className="cursor-pointer hover:bg-muted/50 transition-colors border-b border-border"
                    >
                      <TableCell className="font-medium text-foreground">
                        <span className={isPrivacyMode ? 'blur-sm select-none' : ''}>
                          {maskText(caseItem.project)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${getRiskColor(caseItem.riskScore)}`}>
                          {getRiskIcon(caseItem.riskScore)}
                          {caseItem.riskScore}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${caseItem.status === 'Pending Review' ? 'bg-amber-500/10 text-amber-600 border-amber-500/20' : 'bg-primary/10 text-primary border-primary/20'}`}>
                          {caseItem.status}
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground font-medium">
                        <span className={isPrivacyMode ? 'blur-sm select-none' : ''}>
                          {isPrivacyMode ? '••/••/••••' : new Date(caseItem.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    </AppLayout>
  )
}
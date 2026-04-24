import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText, Shield, BookOpen, Clock, Mail, CheckCircle2, XCircle, Loader2, GitCommit, GitBranch } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { AppLayout } from '@/components/layout/AppLayout'
import { toast } from "sonner"

export function CaseDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [caseData, setCaseData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)

  // Fetch real data on load
  useEffect(() => {
    const fetchCase = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/api/cases/${id}`)
        if (!res.ok) throw new Error("Case not found")
        const data = await res.json()
        setCaseData(data)
      } catch (err) {
        console.error(err)
        toast.error("Failed to load case details")
      } finally {
        setIsLoading(false)
      }
    }
    
    if (import.meta.env.VITE_USE_MOCK_DATA !== 'true') {
      fetchCase()
    } else {
      // Fallback for mock mode
      setCaseData({ project_name: 'Mock Project', risk_score: 'Medium', status: 'Pending Review' })
      setIsLoading(false)
    }
  }, [id])

  const handleDecision = async (decision: 'approved' | 'rejected') => {
    if (decision === 'approved') setIsApproving(true)
    if (decision === 'rejected') setIsRejecting(true)

    const useMock = import.meta.env.VITE_USE_MOCK_DATA === 'true'

    if (!useMock) {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/cases/${id}/status`, { 
          method: 'PUT', 
          headers: {'Content-Type': 'application/json'}, 
          body: JSON.stringify({ status: decision === 'approved' ? 'Approved' : 'Rejected' }) 
        })
        
        if (!response.ok) throw new Error("Failed to update status")
      } catch (err) {
        toast.error("Network Error", { description: "Could not reach the backend." })
        setIsApproving(false)
        setIsRejecting(false)
        return
      }
    }

    await new Promise(resolve => setTimeout(resolve, 800)) // Artificial delay for UX feel

    if (decision === 'approved') {
      toast.success("Release Approved", { description: `GitHub pipeline for ${caseData?.project_name || id} has been unblocked.` })
    } else {
      toast.error("Release Rejected", { description: `GitHub pipeline for ${caseData?.project_name || id} has been failed.` })
    }

    setTimeout(() => {
      navigate('/dashboard')
    }, 800)
  }

  const isProcessing = isApproving || isRejecting

  // Extract GitHub data safely
  const payload = caseData?.raw_payload || {}
  const repoName = payload.repository?.full_name || caseData?.project_name || 'Unknown Repository'
  const commitSha = payload.pull_request?.head?.sha || payload.after || payload.head_commit?.id || 'N/A'
  const commitUrl = payload.repository?.html_url ? `${payload.repository.html_url}/commit/${commitSha}` : '#'

  return (
    <AppLayout>
      <div className="h-full flex flex-col bg-background">
        <header className="border-b border-border bg-background px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm" onClick={() => navigate('/dashboard')} disabled={isProcessing}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Separator orientation="vertical" className="h-6" />
            <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
              Case Details: <span className="text-primary font-mono text-lg">{id?.split('-')[0]}</span>
            </h1>
          </div>
          
          {caseData && (
             <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${caseData.risk_score === 'High' ? 'bg-red-500/10 text-red-600 border-red-500/20' : caseData.risk_score === 'Medium' ? 'bg-amber-500/10 text-amber-600 border-amber-500/20' : 'bg-green-500/10 text-green-600 border-green-500/20'}`}>
               {caseData.risk_score} Risk
             </div>
          )}
        </header>

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
            
            {/* LEFT PANEL: Context & Metadata */}
            <div className="space-y-6 overflow-y-auto pr-2 pb-6">
              
              <section>
                <h2 className="text-lg font-semibold flex items-center mb-4 text-foreground"><GitBranch className="w-5 h-5 mr-2 text-muted-foreground" />GitHub Context</h2>
                <Card className="p-5 space-y-4 border-border shadow-sm">
                  <div>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Repository</p>
                    <p className="font-medium text-foreground">{repoName}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Target Commit</p>
                    <div className="flex items-center gap-2">
                      <GitCommit className="w-4 h-4 text-muted-foreground" />
                      <a href={commitUrl} target="_blank" rel="noreferrer" className="font-mono text-sm text-primary hover:underline">
                        {commitSha.substring(0, 7)}
                      </a>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Current Status</p>
                    <p className="text-sm font-medium">{caseData?.status}</p>
                  </div>
                </Card>
              </section>

              <Separator className="bg-border" />

              <section>
                <h2 className="text-lg font-semibold flex items-center mb-4 text-foreground"><BookOpen className="w-5 h-5 mr-2 text-muted-foreground" />Documentation Guidelines</h2>
                <div className="grid gap-3">
                  <Card className="p-3 flex items-center gap-3 cursor-pointer hover:bg-muted/50 transition-colors border-border">
                    <div className="bg-primary/10 p-2 rounded"><Shield className="w-5 h-5 text-primary" /></div>
                    <div><p className="font-medium text-sm text-foreground">Security Protocols v4.2</p></div>
                  </Card>
                </div>
              </section>
              
              <Separator className="bg-border" />
              
              <section>
                <h2 className="text-lg font-semibold flex items-center mb-4 text-foreground"><Clock className="w-5 h-5 mr-2 text-muted-foreground" />AI Processing History</h2>
                <div className="space-y-4">
                  <Card className="p-4 border-border">
                    <p className="text-sm text-muted-foreground">Automated payload validation passed. Awaiting human oversight to release pipeline lock.</p>
                  </Card>
                </div>
              </section>
            </div>

            {/* RIGHT PANEL: Email Client & Actions */}
            <Card className="flex flex-col h-full border-border shadow-sm overflow-hidden flex-1 bg-card">
              <div className="bg-muted/50 px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="font-semibold flex items-center text-foreground"><Mail className="w-4 h-4 mr-2" />Draft Decision</h3>
              </div>
              
              <div className="p-4 space-y-4 flex-1 flex flex-col opacity-90">
                <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                  <label className="text-sm font-medium text-muted-foreground text-right">To:</label>
                  <Input defaultValue="release.management@hitachi.com" disabled={isProcessing} className="bg-background" />
                </div>
                <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                  <label className="text-sm font-medium text-muted-foreground text-right">Subject:</label>
                  <Input defaultValue={`Approval Status: ${repoName}`} className="font-medium bg-background" disabled={isProcessing} />
                </div>
                <Separator className="my-2 bg-border" />
                <Textarea 
                  className="flex-1 resize-none p-4 min-h-[250px] bg-background text-foreground"
                  disabled={isProcessing}
                  defaultValue={`Hi Team,\n\nI have reviewed the release candidate for ${repoName} (Commit: ${commitSha.substring(0, 7)}).\n\nPlease process accordingly.\n\nBest regards,\nHitachi AI Advisor Manager`}
                />
              </div>

              {/* Action Buttons */}
              <div className="p-4 bg-muted/50 border-t border-border flex justify-end gap-3 shrink-0">
                <Button 
                  variant="outline" 
                  className="text-red-600 border-red-200 hover:bg-red-500/10 dark:hover:bg-red-900/20"
                  onClick={() => handleDecision('rejected')}
                  disabled={isProcessing || caseData?.status === 'Approved' || caseData?.status === 'Rejected'}
                >
                  {isRejecting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                  Reject Pipeline
                </Button>
                
                <Button 
                  className="bg-green-600 hover:bg-green-700 text-white"
                  onClick={() => handleDecision('approved')}
                  disabled={isProcessing || caseData?.status === 'Approved' || caseData?.status === 'Rejected'}
                >
                  {isApproving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                  Approve Pipeline
                </Button>
              </div>
            </Card>
          </main>
        )}
      </div>
    </AppLayout>
  )
}
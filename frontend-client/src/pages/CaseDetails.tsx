import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText, Shield, BookOpen, Clock, Mail, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
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
  
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)

  const handleDecision = async (decision: 'approved' | 'rejected') => {
    if (decision === 'approved') setIsApproving(true)
    if (decision === 'rejected') setIsRejecting(true)

    const useMock = import.meta.env.VITE_USE_MOCK_DATA === 'true'

    if (!useMock) {
      await fetch(`${import.meta.env.VITE_API_URL}/api/cases/${id}/status`, { 
        method: 'PUT', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify({ status: decision === 'approved' ? 'Approved' : 'Rejected' }) 
      })
    }

    await new Promise(resolve => setTimeout(resolve, 1200))

    // Sonner toast syntax
    if (decision === 'approved') {
      toast.success("Release Approved", { description: `Case REQ-${id} has been cleared for deployment.` })
    } else {
      toast.error("Release Rejected", { description: `Case REQ-${id} has been flagged for issues.` })
    }

    setTimeout(() => {
      navigate('/dashboard')
    }, 800)
  }

  const isProcessing = isApproving || isRejecting

  return (
    <AppLayout>
      <div className="h-full flex flex-col bg-background">
        <header className="border-b border-border bg-background px-6 py-4 flex items-center gap-4 shrink-0">
          <Button variant="outline" size="sm" onClick={() => navigate('/dashboard')} disabled={isProcessing}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-xl font-bold text-foreground">
            Case Details: <span className="text-hitachi-blue">REQ-{id}</span>
          </h1>
        </header>

        <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
          
          {/* LEFT PANEL: Same as before */}
          <div className="space-y-6 overflow-y-auto pr-2 pb-6">
            <section>
              <h2 className="text-lg font-semibold flex items-center mb-4"><BookOpen className="w-5 h-5 mr-2 text-muted-foreground" />Documentation</h2>
              <div className="grid gap-3">
                <Card className="p-3 flex items-center gap-3 cursor-pointer hover:bg-muted transition-colors">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded"><Shield className="w-5 h-5 text-blue-600" /></div>
                  <div><p className="font-medium text-sm">Security Protocols v4.2</p></div>
                </Card>
              </div>
            </section>
            <Separator />
            <section>
              <h2 className="text-lg font-semibold flex items-center mb-4"><Clock className="w-5 h-5 mr-2 text-muted-foreground" />History</h2>
              <div className="space-y-4">
                <Card className="p-4"><p className="text-sm text-muted-foreground">Automated security scanning passed.</p></Card>
              </div>
            </section>
          </div>

          {/* RIGHT PANEL: Email Client & Actions */}
          <Card className="flex flex-col h-full border-border shadow-sm overflow-hidden flex-1">
            <div className="bg-muted px-4 py-3 border-b flex items-center justify-between">
              <h3 className="font-semibold flex items-center"><Mail className="w-4 h-4 mr-2" />Draft Decision</h3>
            </div>
            
            <div className="p-4 space-y-4 flex-1 flex flex-col opacity-90">
              <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                <label className="text-sm font-medium text-muted-foreground text-right">To:</label>
                <Input defaultValue="release.management@hitachi.com" disabled={isProcessing} />
              </div>
              <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                <label className="text-sm font-medium text-muted-foreground text-right">Subject:</label>
                <Input defaultValue={`Approval Status: Release Case REQ-${id}`} className="font-medium" disabled={isProcessing} />
              </div>
              <Separator className="my-2" />
              <Textarea 
                className="flex-1 resize-none p-4 min-h-[250px]"
                disabled={isProcessing}

                defaultValue={`Hi Team,\n\nI have reviewed the details for Release Case REQ-${id}.\n\nPlease process accordingly.\n\nBest regards,\nAI Advisor`}
              />
            </div>

            {/* Action Buttons */}
            <div className="p-4 bg-muted/50 border-t flex justify-end gap-3 shrink-0">
              <Button 
                variant="outline" 
                className="text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700"
                onClick={() => handleDecision('rejected')}
                disabled={isProcessing}
              >
                {isRejecting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                Reject Release
              </Button>
              
              <Button 
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={() => handleDecision('approved')}
                disabled={isProcessing}
              >
                {isApproving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                Approve Release
              </Button>
            </div>
          </Card>
        </main>
      </div>
    </AppLayout>
  )
}
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText, Shield, BookOpen, Clock, Mail, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { AppLayout } from '@/components/layout/AppLayout'

export function CaseDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  return (
    <AppLayout>
      <div className="h-full flex flex-col bg-background">
        {/* Page Sub-Header */}
        <header className="border-b border-border bg-background px-6 py-4 flex items-center gap-4 shrink-0">
          <Button variant="outline" size="sm" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-xl font-bold text-foreground">
            Case Details: <span className="text-hitachi-blue">REQ-{id}</span>
          </h1>
        </header>

        {/* Split Screen Layout */}
        <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
          
          {/* LEFT PANEL: Information Hub */}
          <div className="space-y-6 overflow-y-auto pr-2 pb-6">
            
            {/* Documentation Section */}
            <section>
              <h2 className="text-lg font-semibold text-foreground flex items-center mb-4">
                <BookOpen className="w-5 h-5 mr-2 text-muted-foreground" />
                Documentation & Guidelines
              </h2>
              <div className="grid gap-3">
                <Card className="p-3 flex items-center gap-3 cursor-pointer hover:bg-muted transition-colors">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded">
                    <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="font-medium text-sm text-foreground">Security Protocols v4.2</p>
                    <p className="text-xs text-muted-foreground">Required compliance checks</p>
                  </div>
                </Card>
                <Card className="p-3 flex items-center gap-3 cursor-pointer hover:bg-muted transition-colors">
                  <div className="bg-green-100 dark:bg-green-900/30 p-2 rounded">
                    <FileText className="w-5 h-5 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="font-medium text-sm text-foreground">Release Playbook</p>
                    <p className="text-xs text-muted-foreground">Standard operating procedure</p>
                  </div>
                </Card>
              </div>
            </section>

            <Separator />

            {/* Email History Timeline */}
            <section>
              <h2 className="text-lg font-semibold text-foreground flex items-center mb-4">
                <Clock className="w-5 h-5 mr-2 text-muted-foreground" />
                Communication History
              </h2>
              <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-linear-to-b before:from-transparent before:via-border before:to-transparent">
                
                <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full border border-border bg-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <Card className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-sm">DevOps Team</span>
                      <span className="text-xs text-muted-foreground">2 hours ago</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Initial release bundle submitted for automated security scanning. All tests passed.</p>
                  </Card>
                </div>

                <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full border border-border bg-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <Card className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-sm">QA Lead</span>
                      <span className="text-xs text-muted-foreground">Yesterday</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Staging environment tests verified. Awaiting final architectural review.</p>
                  </Card>
                </div>

              </div>
            </section>
          </div>

          {/* RIGHT PANEL: Email Client */}
          <Card className="flex flex-col h-full border-border shadow-sm overflow-hidden flex-1">
            <div className="bg-muted px-4 py-3 border-b border-border flex items-center justify-between">
              <h3 className="font-semibold text-foreground flex items-center">
                <Mail className="w-4 h-4 mr-2" />
                Draft Decision
              </h3>
              <span className="text-xs font-medium px-2 py-1 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 rounded-full">
                Pending Action
              </span>
            </div>
            
            <div className="p-4 space-y-4 flex-1 flex flex-col">
              <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                <label className="text-sm font-medium text-muted-foreground text-right">To:</label>
                <Input defaultValue="release.management@hitachi.com" className="bg-background" />
              </div>
              <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                <label className="text-sm font-medium text-muted-foreground text-right">Cc:</label>
                <Input defaultValue="qa-team@hitachi.com" className="bg-background" />
              </div>
              <div className="grid grid-cols-[60px_1fr] items-center gap-2">
                <label className="text-sm font-medium text-muted-foreground text-right">Subject:</label>
                <Input defaultValue={`Approval Status: Release Case REQ-${id}`} className="bg-background font-medium" />
              </div>
              
              <Separator className="my-2" />
              
              {/* Main Email Body */}
              <Textarea 
                className="flex-1 resize-none bg-background p-4 min-h-75"
                defaultValue={`Hi Team,\n\nI have reviewed the details for Release Case REQ-${id} alongside the current Security Protocols and QA logs.\n\n[   ] APPROVED: Proceed with deployment.\n[   ] REJECTED: Please address the following issues before resubmitting:\n\n1. \n2. \n\nBest regards,\nAI Advisor`}
              />
            </div>

            <div className="p-4 bg-muted/50 border-t border-border flex justify-end gap-3 shrink-0">
              <Button variant="outline">Save Draft</Button>
              <Button className="bg-hitachi-blue hover:bg-hitachi-blue-light text-white">
                <Send className="w-4 h-4 mr-2" />
                Send Decision
              </Button>
            </div>
          </Card>

        </main>
      </div>
    </AppLayout>
  )
}
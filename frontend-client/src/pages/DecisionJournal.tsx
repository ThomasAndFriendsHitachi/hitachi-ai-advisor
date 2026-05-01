import { useState } from 'react'
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  User,
  ArrowRight,
  Download,
  ChevronRight,
  Clock,
  CheckSquare,
  XSquare,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { AppLayout } from '@/components/layout/AppLayout'
import { MOCK_DECISION_JOURNAL_DATA } from '@/mocks/decisionJournalMock'
import { PublishedRelease, DecisionPathStep } from '@/types/decisionJournal'

export function DecisionJournal() {
  const data = MOCK_DECISION_JOURNAL_DATA
  const latestRelease = data.latestRelease
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>(latestRelease.id)

  const selectedRelease =
    latestRelease.id === selectedReleaseId
      ? latestRelease
      : data.previousReleases.find(r => r.id === selectedReleaseId) || latestRelease

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDateShort = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <AppLayout>
      <div className="h-full flex flex-col bg-background overflow-hidden">
        {/* ========== HEADER ========== */}
        <header className="border-b border-border bg-background px-6 py-6 shrink-0">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground flex items-center gap-3 mb-2">
                <FileText className="w-8 h-8 text-hitachi-blue" />
                Decision Journal
              </h1>
              <p className="text-muted-foreground">
                Documents published releases, approved changes, resolved conflicts, and historical analysis reports
              </p>
            </div>
            <Button className="bg-hitachi-blue hover:bg-hitachi-blue/90 text-white flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Report
            </Button>
          </div>
        </header>

        {/* ========== MAIN CONTENT (SCROLLABLE) ========== */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-6 py-6 space-y-8">
            {/* ========== LAYER 1: LATEST RELEASE CARD ========== */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-green-600" />
                Latest Published Release
              </h2>
              <Card className="border border-border bg-card p-6 space-y-4">
                {/* Version & Date */}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-foreground">
                      Release {latestRelease.baseline.version}
                    </h3>
                    <p className="text-sm text-muted-foreground flex items-center gap-2 mt-2">
                      <Calendar className="w-4 h-4" />
                      Published {formatDate(latestRelease.publishedAt)}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300 mb-2">
                      Final Approval Completed
                    </Badge>
                  </div>
                </div>

                <Separator />

                {/* Status Badges */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckSquare className="w-5 h-5 text-blue-600" />
                      <span className="font-semibold text-blue-900">{latestRelease.summary.approvedChanges}</span>
                    </div>
                    <p className="text-sm text-blue-700">Approved Changes</p>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      <span className="font-semibold text-yellow-900">{latestRelease.summary.resolvedConflicts}</span>
                    </div>
                    <p className="text-sm text-yellow-700">Resolved Conflicts</p>
                  </div>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-5 h-5 text-purple-600" />
                      <span className="font-semibold text-purple-900">
                        {latestRelease.summary.averageApprovalTimeHours.toFixed(1)}h
                      </span>
                    </div>
                    <p className="text-sm text-purple-700">Avg Approval Time</p>
                  </div>
                </div>

                <Separator />

                {/* CTA Button */}
                <div className="flex justify-end">
                  <Button className="bg-hitachi-blue hover:bg-hitachi-blue/90 text-white flex items-center gap-2">
                    Open Full Report
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            </section>

            {/* ========== LAYER 2: DEEP DIVE - TWO COLUMNS ========== */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-foreground">Deep Dive: Approved Changes & Resolved Conflicts</h2>
              <div className="grid grid-cols-2 gap-6">
                {/* LEFT: Approved Changes */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    Approved Changes
                  </h3>
                  <div className="space-y-2">
                    {selectedRelease.approvedRequirements.map(req => (
                      <Card key={req.id} className="border border-border bg-card p-4 hover:bg-muted transition-colors">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
                              <div className="min-w-0">
                                <p className="font-mono text-sm font-semibold text-hitachi-blue">{req.id}</p>
                                <p className="text-sm font-medium text-foreground line-clamp-2">{req.title}</p>
                              </div>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground">{req.affectedObject}</p>
                          <div className="flex items-center justify-between pt-2 border-t border-border">
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <User className="w-3 h-3" />
                              <span>{req.approvedBy?.name || 'N/A'}</span>
                            </div>
                            {req.approvedBy && (
                              <span className="text-xs text-muted-foreground">
                                {formatDateShort(req.approvedBy.timestamp)}
                              </span>
                            )}
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>

                {/* RIGHT: Resolved Conflicts */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    Resolved Conflicts
                  </h3>
                  <div className="space-y-2">
                    {selectedRelease.resolvedConflicts.map(conflict => (
                      <Card key={conflict.id} className="border border-border bg-card p-4 hover:bg-muted transition-colors">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 shrink-0" />
                              <div className="min-w-0">
                                <p className="text-sm font-semibold text-foreground line-clamp-2">
                                  {conflict.conflictIssue}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">
                                  Severity: <span className="capitalize">{conflict.severity}</span>
                                </p>
                              </div>
                            </div>
                          </div>
                          {conflict.resolution && (
                            <>
                              <p className="text-xs text-muted-foreground border-t border-border pt-2">
                                <span className="font-semibold capitalize">{conflict.resolution.method}</span> resolution
                                by {conflict.resolution.resolvedBy.name} ({conflict.resolution.resolvedBy.role})
                              </p>
                              <p className="text-xs text-muted-foreground italic">{conflict.resolution.notes}</p>
                            </>
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* ========== LAYER 2B: RELEASE DECISION PATH (TIMELINE) ========== */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-foreground">Release Decision Path</h2>
              <Card className="border border-border bg-card p-6">
                <div className="space-y-4">
                  {selectedRelease.decisionPath.map((step, idx) => (
                    <div key={step.id} className="relative">
                      {/* Timeline line (except last step) */}
                      {idx < selectedRelease.decisionPath.length - 1 && (
                        <div className="absolute left-5 top-10 bottom-0 w-0.5 bg-border" />
                      )}

                      {/* Step item */}
                      <div className="flex gap-4">
                        {/* Circle indicator */}
                        <div className="relative z-10 flex-shrink-0">
                          <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                              step.status === 'completed'
                                ? 'bg-green-100 border-green-600'
                                : step.status === 'in_progress'
                                  ? 'bg-blue-100 border-blue-600'
                                  : 'bg-muted border-border'
                            }`}
                          >
                            {step.status === 'completed' ? (
                              <CheckSquare className="w-5 h-5 text-green-600" />
                            ) : step.status === 'in_progress' ? (
                              <Clock className="w-5 h-5 text-blue-600 animate-spin" />
                            ) : (
                              <div className="w-2 h-2 bg-muted-foreground rounded-full" />
                            )}
                          </div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 pb-4">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-semibold text-foreground">{step.name}</h4>
                              <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
                            </div>
                            <span className="text-xs font-mono text-muted-foreground">Step {step.stepNumber}</span>
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            {step.actor && (
                              <div className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                <span>
                                  {step.actor.name} ({step.actor.role})
                                </span>
                              </div>
                            )}
                            <span>{formatDate(step.timestamp)}</span>
                            {step.duration && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {(step.duration / 3600000).toFixed(1)}h
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </section>

            {/* ========== LAYER 3: HISTORICAL RELEASES ========== */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold text-foreground">Previous Published Releases</h2>
              <div className="space-y-2">
                {data.previousReleases.map(release => (
                  <Card
                    key={release.id}
                    className={`border p-4 cursor-pointer transition-colors ${
                      selectedReleaseId === release.id
                        ? 'border-hitachi-blue bg-blue-50'
                        : 'border-border bg-card hover:bg-muted'
                    }`}
                    onClick={() => setSelectedReleaseId(release.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="text-lg font-semibold text-foreground">Release {release.baseline.version}</h4>
                          <Badge variant="outline">{formatDateShort(release.publishedAt)}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {release.summary.approvedChanges} approved changes • {release.summary.resolvedConflicts}{' '}
                          conflicts resolved • Published by {release.publishedBy.name}
                        </p>
                      </div>
                      <Button variant="outline" className="ml-4">
                        Open Report
                        <ChevronRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            </section>

            {/* Footer spacing */}
            <div className="h-4" />
          </div>
        </div>
      </div>
    </AppLayout>
  )
}

/**
 * DecisionJournalPreview Component
 *
 * A compact card to embed in CaseDetails page showing the latest decision journal entry.
 * Displays key release information, recent changes, and a link to the full journal.
 */

import { Link } from 'react-router-dom'
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  CheckSquare,
  Calendar,
  User,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { MOCK_DECISION_JOURNAL_DATA } from '@/mocks/decisionJournalMock'

interface DecisionJournalPreviewProps {
  compact?: boolean // Even more condensed version if true
}

export function DecisionJournalPreview({ compact = false }: DecisionJournalPreviewProps) {
  const latestRelease = MOCK_DECISION_JOURNAL_DATA.latestRelease

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (compact) {
    // Ultra-compact version for tight spaces
    return (
      <Card className="border border-border bg-card p-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="w-4 h-4 text-hitachi-blue shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-semibold text-foreground">Latest Release {latestRelease.baseline.version}</p>
              <p className="text-xs text-muted-foreground">{latestRelease.summary.approvedChanges} approved changes</p>
            </div>
          </div>
          <Link to="/decision-journal">
            <Button variant="outline" size="sm" className="flex items-center gap-1">
              <span className="hidden sm:inline text-xs">View</span>
              <ArrowRight className="w-3 h-3" />
            </Button>
          </Link>
        </div>
      </Card>
    )
  }

  // Standard preview version (default)
  return (
    <Card className="border border-border bg-card p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-hitachi-blue" />
          <h3 className="text-lg font-bold text-foreground">Latest Decision Journal</h3>
        </div>
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
          Published
        </Badge>
      </div>

      <Separator />

      {/* Release Info */}
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-mono font-bold text-hitachi-blue">Release {latestRelease.baseline.version}</h4>
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            <Calendar className="w-3 h-3" />
            {formatDate(latestRelease.publishedAt)}
          </p>
        </div>

        {/* Summary Stats - Inline */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-blue-50 border border-blue-200 rounded p-2">
            <div className="flex items-center gap-1 mb-0.5">
              <CheckSquare className="w-4 h-4 text-blue-600" />
              <span className="font-semibold text-sm text-blue-900">{latestRelease.summary.approvedChanges}</span>
            </div>
            <p className="text-xs text-blue-700">Changes</p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
            <div className="flex items-center gap-1 mb-0.5">
              <AlertTriangle className="w-4 h-4 text-yellow-600" />
              <span className="font-semibold text-sm text-yellow-900">{latestRelease.summary.resolvedConflicts}</span>
            </div>
            <p className="text-xs text-yellow-700">Conflicts</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded p-2">
            <div className="flex items-center gap-1 mb-0.5">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <span className="font-semibold text-sm text-green-900">Approved</span>
            </div>
            <p className="text-xs text-green-700">Status</p>
          </div>
        </div>
      </div>

      {/* Recent Changes Preview */}
      {latestRelease.approvedRequirements.length > 0 && (
        <>
          <Separator />
          <div className="space-y-2">
            <h5 className="text-sm font-semibold text-foreground">Recent Approved Changes</h5>
            <div className="space-y-1">
              {latestRelease.approvedRequirements.slice(0, 2).map(req => (
                <div key={req.id} className="flex items-start gap-2 text-xs">
                  <CheckCircle2 className="w-3 h-3 text-green-600 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="font-mono text-green-700 font-semibold">{req.id}</p>
                    <p className="text-muted-foreground line-clamp-1">{req.title}</p>
                  </div>
                </div>
              ))}
              {latestRelease.approvedRequirements.length > 2 && (
                <p className="text-xs text-muted-foreground px-5">
                  +{latestRelease.approvedRequirements.length - 2} more changes
                </p>
              )}
            </div>
          </div>
        </>
      )}

      {/* Published Info */}
      {latestRelease.publishedBy && (
        <>
          <Separator />
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1 text-muted-foreground">
              <User className="w-3 h-3" />
              <span>Published by {latestRelease.publishedBy.name}</span>
            </div>
          </div>
        </>
      )}

      {/* CTA */}
      <Link to="/decision-journal" className="block pt-2">
        <Button className="w-full bg-hitachi-blue hover:bg-hitachi-blue/90 text-white flex items-center justify-center gap-2">
          View Full Decision Journal
          <ArrowRight className="w-4 h-4" />
        </Button>
      </Link>
    </Card>
  )
}

export default DecisionJournalPreview

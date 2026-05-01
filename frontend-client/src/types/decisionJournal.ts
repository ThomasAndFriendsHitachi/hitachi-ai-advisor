/**
 * Decision Journal Type Definitions
 * 
 * Supports:
 * - Parallel Baselines: Requirements linked to specific baseline versions for continuous deliveries
 * - Abort/Interrupt Signals: Ability to stop running analyses when new requirements arrive
 * - Conflict Override: Force resolution of conflicting requirements
 * - AI Data Management: Historical tracking of all decisions and conflicts
 */

/**
 * Enum for requirement status throughout the decision lifecycle
 */
export enum RequirementStatus {
  PROPOSED = 'proposed',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  SUPERSEDED = 'superseded', // Replaced by newer requirement
}

/**
 * Enum for AI analysis states
 */
export enum AnalysisState {
  IDLE = 'idle',
  RUNNING = 'running',
  COMPLETED = 'completed',
  INTERRUPTED = 'interrupted',
  FAILED = 'failed',
}

/**
 * Signal sent to AI when new requirements arrive during analysis
 */
export interface AbortSignal {
  id: string
  signalTimestamp: string
  triggeringRequirementId: string
  reason: string // 'new_requirement_received' | 'manual_user_stop'
}

/**
 * Baseline version that freezes a snapshot of requirements
 * Enables parallel work on different baseline versions
 */
export interface Baseline {
  id: string
  version: string // e.g., 'v1.8.2'
  releaseDate: string // ISO date when published
  baselineHash: string // Hash of all requirements in this baseline
  status: 'active' | 'archived'
  requirementCount: number
  conflictCount: number
  approvedChanges: number
}

/**
 * Individual requirement or change
 */
export interface Requirement {
  id: string // e.g., 'REQ-AR-04'
  title: string
  description: string
  affectedObject: string // e.g., 'Deployment baseline', 'API contract'
  status: RequirementStatus
  proposedBy: {
    id: string
    name: string
    role: string
  }
  approvedBy?: {
    id: string
    name: string
    role: string
    timestamp: string
  }
  sourceEvidence: SourceEvidence[]
  baselineId: string // Link to specific baseline/version
  createdAt: string
  updatedAt: string
}

/**
 * Evidence source (email, PR, file, etc.)
 */
export interface SourceEvidence {
  id: string
  type: 'email' | 'pull_request' | 'file' | 'document' | 'slack_message'
  reference: string // URL or identifier
  timestamp: string
  summary: string
}

/**
 * Conflict between requirements
 */
export interface RequirementConflict {
  id: string
  conflictIssue: string // e.g., 'Missing validation evidence'
  requirement1: Requirement
  requirement2: Requirement
  severity: 'low' | 'medium' | 'high'
  status: 'detected' | 'resolved' | 'overridden'
  resolution?: ConflictResolution
}

/**
 * How a conflict was resolved
 */
export interface ConflictResolution {
  id: string
  method: 'automatic' | 'manual' | 'override'
  resolvedAt: string
  resolvedBy: {
    id: string
    name: string
    role: string
  }
  supersededRequirementId: string // Requirement that was deprecated
  retainedRequirementId: string // Requirement that was kept
  notes: string
}

/**
 * AI analysis run that processed requirements and detected conflicts
 */
export interface AIAnalysisRun {
  id: string
  baselineId: string
  analysisState: AnalysisState
  startTime: string
  endTime?: string
  abortSignal?: AbortSignal
  suggestedConflicts: RequirementConflict[]
  processingTimeMs?: number
  inputRequirementCount: number
  outputApprovedCount: number
}

/**
 * Published release document (historical record)
 */
export interface PublishedRelease {
  id: string
  baseline: Baseline
  analysisRuns: AIAnalysisRun[]
  approvedRequirements: Requirement[]
  resolvedConflicts: RequirementConflict[]
  decisionPath: DecisionPathStep[]
  publishedAt: string
  publishedBy: {
    id: string
    name: string
    role: string
  }
  summary: {
    totalChanges: number
    approvedChanges: number
    resolvedConflicts: number
    averageApprovalTimeHours: number
  }
}

/**
 * Step in the decision workflow
 */
export interface DecisionPathStep {
  id: string
  stepNumber: number
  name: string // 'Trigger received', 'AI suggestion generated', etc.
  description: string
  timestamp: string
  status: 'completed' | 'in_progress' | 'pending' | 'skipped'
  actor?: {
    id: string
    name: string
    role: string
  }
  duration?: number // milliseconds
}

/**
 * Decision Journal data model
 */
export interface DecisionJournalData {
  latestRelease: PublishedRelease
  previousReleases: PublishedRelease[]
  baselines: Baseline[]
}

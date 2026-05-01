/**
 * Mock data for Decision Journal
 * 
 * Demonstrates all features:
 * - Parallel baselines with versioning
 * - Abort signals for interrupted analyses
 * - Conflict detection and resolution
 * - Complete decision path timeline
 * - Historical releases
 */

import {
  RequirementStatus,
  AnalysisState,
  type Baseline,
  type Requirement,
  type RequirementConflict,
  type AIAnalysisRun,
  type PublishedRelease,
  type DecisionPathStep,
  type DecisionJournalData,
  type AbortSignal,
} from '@/types/decisionJournal'

// ============= BASELINES =============
const BASELINES: Baseline[] = [
  {
    id: 'baseline-1-8-2',
    version: 'v1.8.2',
    releaseDate: '2026-05-01T10:30:00Z',
    baselineHash: 'h7f3a9d2e1b4c8f6a',
    status: 'active',
    requirementCount: 47,
    conflictCount: 3,
    approvedChanges: 44,
  },
  {
    id: 'baseline-1-8-1',
    version: 'v1.8.1',
    releaseDate: '2026-04-15T14:20:00Z',
    baselineHash: 'h5e2b8c1d4a7f9x3k',
    status: 'archived',
    requirementCount: 41,
    conflictCount: 2,
    approvedChanges: 39,
  },
  {
    id: 'baseline-1-8-0',
    version: 'v1.8.0',
    releaseDate: '2026-04-01T09:00:00Z',
    baselineHash: 'h3c9x2d1a8b5f7e4k',
    status: 'archived',
    requirementCount: 38,
    conflictCount: 1,
    approvedChanges: 37,
  },
]

// ============= REQUIREMENTS =============
const REQUIREMENTS: Requirement[] = [
  {
    id: 'REQ-AR-04',
    title: 'Deployment Baseline Validation',
    description: 'Ensure all deployment scripts are validated against the baseline',
    affectedObject: 'Deployment baseline',
    status: RequirementStatus.APPROVED,
    proposedBy: {
      id: 'user-1',
      name: 'Elena Rossi',
      role: 'Requirements Engineer',
    },
    approvedBy: {
      id: 'user-5',
      name: 'Marco Fermi',
      role: 'QA Lead',
      timestamp: '2026-05-01T09:15:00Z',
    },
    sourceEvidence: [
      {
        id: 'ev-1',
        type: 'pull_request',
        reference: 'https://github.com/hitachi/arra/pull/423',
        timestamp: '2026-04-30T15:45:00Z',
        summary: 'PR: Add baseline validation pipeline',
      },
      {
        id: 'ev-2',
        type: 'document',
        reference: 'Deployment_Process_v2.0.pdf',
        timestamp: '2026-04-28T10:30:00Z',
        summary: 'Deployment process documentation',
      },
    ],
    baselineId: 'baseline-1-8-2',
    createdAt: '2026-04-28T08:00:00Z',
    updatedAt: '2026-05-01T09:15:00Z',
  },
  {
    id: 'REQ-AR-05',
    title: 'Authentication Protocol Update',
    description: 'Update OAuth2 implementation to support OIDC',
    affectedObject: 'Authentication Service',
    status: RequirementStatus.APPROVED,
    proposedBy: {
      id: 'user-2',
      name: 'Andrea Gallo',
      role: 'Security Architect',
    },
    approvedBy: {
      id: 'user-3',
      name: 'Dr. Paolo Verdi',
      role: 'Systems Engineer',
      timestamp: '2026-05-01T08:45:00Z',
    },
    sourceEvidence: [
      {
        id: 'ev-3',
        type: 'email',
        reference: 'Security_Discussion_Apr28.eml',
        timestamp: '2026-04-28T16:20:00Z',
        summary: 'Email discussion on OAuth2 upgrade',
      },
    ],
    baselineId: 'baseline-1-8-2',
    createdAt: '2026-04-29T11:00:00Z',
    updatedAt: '2026-05-01T08:45:00Z',
  },
  {
    id: 'REQ-AR-06',
    title: 'Performance Optimization for Large Datasets',
    description: 'Index optimization to improve query performance',
    affectedObject: 'Database Layer',
    status: RequirementStatus.APPROVED,
    proposedBy: {
      id: 'user-4',
      name: 'Giulia Colombo',
      role: 'Database Architect',
    },
    approvedBy: {
      id: 'user-5',
      name: 'Marco Fermi',
      role: 'QA Lead',
      timestamp: '2026-05-01T10:00:00Z',
    },
    sourceEvidence: [
      {
        id: 'ev-4',
        type: 'file',
        reference: 'performance_analysis.xlsx',
        timestamp: '2026-04-30T13:30:00Z',
        summary: 'Query performance benchmarks',
      },
    ],
    baselineId: 'baseline-1-8-2',
    createdAt: '2026-04-30T09:00:00Z',
    updatedAt: '2026-05-01T10:00:00Z',
  },
]

// ============= CONFLICTS =============
const CONFLICTS: RequirementConflict[] = [
  {
    id: 'CONF-001',
    conflictIssue: 'Missing validation evidence for deployment scripts',
    requirement1: {
      ...REQUIREMENTS[0],
      id: 'REQ-AR-04',
    },
    requirement2: {
      id: 'REQ-AR-07',
      title: 'Quick-release pipeline without full validation',
      description: 'Allow fast-track releases for hotfixes',
      affectedObject: 'CI/CD Pipeline',
      status: RequirementStatus.REJECTED,
      proposedBy: {
        id: 'user-6',
        name: 'Luca Bianchi',
        role: 'DevOps Engineer',
      },
      sourceEvidence: [],
      baselineId: 'baseline-1-8-2',
      createdAt: '2026-04-29T14:00:00Z',
      updatedAt: '2026-05-01T09:30:00Z',
    },
    severity: 'high',
    status: 'resolved',
    resolution: {
      id: 'res-001',
      method: 'manual',
      resolvedAt: '2026-05-01T09:30:00Z',
      resolvedBy: {
        id: 'user-5',
        name: 'Marco Fermi',
        role: 'QA Lead',
      },
      supersededRequirementId: 'REQ-AR-07',
      retainedRequirementId: 'REQ-AR-04',
      notes: 'Full validation is mandatory for production releases. Fast-track only for hotfix patches with QA approval.',
    },
  },
  {
    id: 'CONF-002',
    conflictIssue: 'OAuth2 vs legacy auth system incompatibility',
    requirement1: {
      ...REQUIREMENTS[1],
      id: 'REQ-AR-05',
    },
    requirement2: {
      id: 'REQ-AR-08',
      title: 'Maintain backward compatibility with legacy clients',
      description: 'Keep existing auth tokens valid during transition',
      affectedObject: 'Authentication Service',
      status: RequirementStatus.APPROVED,
      proposedBy: {
        id: 'user-7',
        name: 'Roberto Mancini',
        role: 'Integration Lead',
      },
      approvedBy: {
        id: 'user-3',
        name: 'Dr. Paolo Verdi',
        role: 'Systems Engineer',
        timestamp: '2026-05-01T08:20:00Z',
      },
      sourceEvidence: [],
      baselineId: 'baseline-1-8-2',
      createdAt: '2026-04-30T10:00:00Z',
      updatedAt: '2026-05-01T08:20:00Z',
    },
    severity: 'medium',
    status: 'resolved',
    resolution: {
      id: 'res-002',
      method: 'override',
      resolvedAt: '2026-05-01T09:00:00Z',
      resolvedBy: {
        id: 'user-3',
        name: 'Dr. Paolo Verdi',
        role: 'Systems Engineer',
      },
      supersededRequirementId: 'REQ-AR-08',
      retainedRequirementId: 'REQ-AR-05',
      notes: 'Legacy auth will be deprecated in v2.0. Transition window of 6 months provided for clients.',
    },
  },
  {
    id: 'CONF-003',
    conflictIssue: 'Database index strategy incompatible with existing schema',
    requirement1: {
      ...REQUIREMENTS[2],
      id: 'REQ-AR-06',
    },
    requirement2: {
      id: 'REQ-AR-09',
      title: 'Zero-downtime deployment requirement',
      description: 'Schema changes must not cause service interruption',
      affectedObject: 'Database Layer',
      status: RequirementStatus.APPROVED,
      proposedBy: {
        id: 'user-8',
        name: 'Francesca Rossi',
        role: 'Release Manager',
      },
      approvedBy: {
        id: 'user-5',
        name: 'Marco Fermi',
        role: 'QA Lead',
        timestamp: '2026-05-01T09:45:00Z',
      },
      sourceEvidence: [],
      baselineId: 'baseline-1-8-2',
      createdAt: '2026-04-30T11:00:00Z',
      updatedAt: '2026-05-01T09:45:00Z',
    },
    severity: 'medium',
    status: 'resolved',
    resolution: {
      id: 'res-003',
      method: 'automatic',
      resolvedAt: '2026-05-01T09:20:00Z',
      resolvedBy: {
        id: 'user-1',
        name: 'Elena Rossi',
        role: 'Requirements Engineer',
      },
      supersededRequirementId: '',
      retainedRequirementId: 'REQ-AR-06',
      notes: 'Index creation uses online index building to avoid downtime. Both requirements can coexist.',
    },
  },
]

// ============= ABORT SIGNALS =============
const ABORT_SIGNAL_EXAMPLE: AbortSignal = {
  id: 'abort-001',
  signalTimestamp: '2026-05-01T07:45:00Z',
  triggeringRequirementId: 'REQ-AR-05',
  reason: 'new_requirement_received',
}

// ============= AI ANALYSIS RUNS =============
const AI_ANALYSIS_RUNS: AIAnalysisRun[] = [
  {
    id: 'analysis-run-001',
    baselineId: 'baseline-1-8-2',
    analysisState: AnalysisState.COMPLETED,
    startTime: '2026-04-30T22:00:00Z',
    endTime: '2026-05-01T05:30:00Z',
    suggestedConflicts: CONFLICTS,
    processingTimeMs: 29400000,
    inputRequirementCount: 47,
    outputApprovedCount: 44,
  },
]

// ============= DECISION PATH =============
const DECISION_PATH_STEPS: DecisionPathStep[] = [
  {
    id: 'step-1',
    stepNumber: 1,
    name: 'Trigger received',
    description: 'New requirements batch submitted via GitHub webhook',
    timestamp: '2026-04-30T20:30:00Z',
    status: 'completed',
    actor: {
      id: 'user-6',
      name: 'Luca Bianchi',
      role: 'DevOps Engineer',
    },
    duration: 300000,
  },
  {
    id: 'step-2',
    stepNumber: 2,
    name: 'AI suggestion generated',
    description: 'Hitachi AI agent analyzed all 47 requirements and detected conflicts',
    timestamp: '2026-05-01T05:30:00Z',
    status: 'completed',
    actor: {
      id: 'ai-001',
      name: 'ARRA AI Agent',
      role: 'AI Analyzer',
    },
    duration: 29400000,
  },
  {
    id: 'step-3',
    stepNumber: 3,
    name: 'Conflict detected',
    description: '3 conflicts identified: deployment validation, auth incompatibility, schema changes',
    timestamp: '2026-05-01T05:31:00Z',
    status: 'completed',
    actor: {
      id: 'ai-001',
      name: 'ARRA AI Agent',
      role: 'AI Analyzer',
    },
    duration: 60000,
  },
  {
    id: 'step-4',
    stepNumber: 4,
    name: 'Evidence added',
    description: 'AI gathered 8 pieces of evidence from PRs, emails, and documentation',
    timestamp: '2026-05-01T06:00:00Z',
    status: 'completed',
    actor: {
      id: 'ai-001',
      name: 'ARRA AI Agent',
      role: 'AI Analyzer',
    },
    duration: 1800000,
  },
  {
    id: 'step-5',
    stepNumber: 5,
    name: 'Decision approved',
    description: 'Stakeholders approved all recommendations and conflict resolutions',
    timestamp: '2026-05-01T09:30:00Z',
    status: 'completed',
    actor: {
      id: 'user-5',
      name: 'Marco Fermi',
      role: 'QA Lead',
    },
    duration: 12600000,
  },
  {
    id: 'step-6',
    stepNumber: 6,
    name: 'Version published',
    description: 'Release v1.8.2 published with 44 approved changes and 3 resolved conflicts',
    timestamp: '2026-05-01T10:30:00Z',
    status: 'completed',
    actor: {
      id: 'user-8',
      name: 'Francesca Rossi',
      role: 'Release Manager',
    },
    duration: 3600000,
  },
]

// ============= LATEST PUBLISHED RELEASE =============
const LATEST_RELEASE: PublishedRelease = {
  id: 'release-1-8-2',
  baseline: BASELINES[0],
  analysisRuns: AI_ANALYSIS_RUNS,
  approvedRequirements: REQUIREMENTS.filter(r => r.status === RequirementStatus.APPROVED),
  resolvedConflicts: CONFLICTS,
  decisionPath: DECISION_PATH_STEPS,
  publishedAt: '2026-05-01T10:30:00Z',
  publishedBy: {
    id: 'user-8',
    name: 'Francesca Rossi',
    role: 'Release Manager',
  },
  summary: {
    totalChanges: 47,
    approvedChanges: 44,
    resolvedConflicts: 3,
    averageApprovalTimeHours: 3.5,
  },
}

// ============= PREVIOUS RELEASES =============
const PREVIOUS_RELEASES: PublishedRelease[] = [
  {
    id: 'release-1-8-1',
    baseline: BASELINES[1],
    analysisRuns: [],
    approvedRequirements: REQUIREMENTS.slice(0, 2),
    resolvedConflicts: CONFLICTS.slice(0, 2),
    decisionPath: DECISION_PATH_STEPS.slice(0, 5),
    publishedAt: '2026-04-15T14:20:00Z',
    publishedBy: {
      id: 'user-8',
      name: 'Francesca Rossi',
      role: 'Release Manager',
    },
    summary: {
      totalChanges: 41,
      approvedChanges: 39,
      resolvedConflicts: 2,
      averageApprovalTimeHours: 4.2,
    },
  },
  {
    id: 'release-1-8-0',
    baseline: BASELINES[2],
    analysisRuns: [],
    approvedRequirements: REQUIREMENTS.slice(0, 1),
    resolvedConflicts: CONFLICTS.slice(0, 1),
    decisionPath: DECISION_PATH_STEPS.slice(0, 4),
    publishedAt: '2026-04-01T09:00:00Z',
    publishedBy: {
      id: 'user-8',
      name: 'Francesca Rossi',
      role: 'Release Manager',
    },
    summary: {
      totalChanges: 38,
      approvedChanges: 37,
      resolvedConflicts: 1,
      averageApprovalTimeHours: 5.1,
    },
  },
]

// ============= COMPLETE DECISION JOURNAL DATA =============
export const MOCK_DECISION_JOURNAL_DATA: DecisionJournalData = {
  latestRelease: LATEST_RELEASE,
  previousReleases: PREVIOUS_RELEASES,
  baselines: BASELINES,
}

export default MOCK_DECISION_JOURNAL_DATA

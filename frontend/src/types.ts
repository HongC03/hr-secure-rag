export interface User {
  id: string
  name: string
  role: string
  department: string
  label: string
  loginName: string | null
}

export interface Citation {
  id: string
  title: string
  classification: string
}

export interface AnswerResponse {
  status: string
  correlationId: string
  answer: string
  citations: Citation[]
  controls: string[]
  pipeline: string
  error?: string
}

export interface AuditEvent {
  timestamp: string
  correlation_id: string
  actor: string
  action: string
  outcome: string
  returned_document_count: number
  latency_ms: number
  controls: string[]
}

export interface HealthResponse {
  status: string
  policyVersion: string
}

export interface MeResponse {
  user: User | null
  policyVersion: string
}

export interface AuditResponse {
  events: AuditEvent[]
  policyVersion: string
}

export interface AuthSubmission {
  registering: boolean
  userId: string
  fullName: string
  password: string
}

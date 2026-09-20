CREATE EXTENSION IF NOT EXISTS vector;

-- The container supplies this only at initialization through its environment.
-- Production must provision the role through its secrets/IAM workflow.
\getenv app_password POSTGRES_APP_PASSWORD
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', 'peoplevault_app', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'peoplevault_app')
\gexec

CREATE TABLE IF NOT EXISTS hr_document_chunks (
  document_id TEXT PRIMARY KEY,
  parent_document_id TEXT NOT NULL,
  chunk_index INTEGER NOT NULL DEFAULT 0,
  title TEXT NOT NULL,
  document_type TEXT NOT NULL,
  classification TEXT NOT NULL,
  owner_id TEXT,
  content TEXT NOT NULL,
  tags TEXT[] NOT NULL DEFAULT '{}',
  embedding VECTOR(768) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Exact authorization filters need conventional indexes in addition to the vector index.
CREATE INDEX IF NOT EXISTS hr_document_chunks_owner_type_idx ON hr_document_chunks (owner_id, document_type);
CREATE INDEX IF NOT EXISTS hr_document_chunks_type_idx ON hr_document_chunks (document_type);
CREATE INDEX IF NOT EXISTS hr_document_chunks_parent_chunk_idx ON hr_document_chunks (parent_document_id, chunk_index);
CREATE INDEX IF NOT EXISTS hr_document_chunks_embedding_hnsw_idx ON hr_document_chunks USING hnsw (embedding vector_cosine_ops);

ALTER TABLE hr_document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr_document_chunks FORCE ROW LEVEL SECURITY;

-- The app must connect as a non-owner, non-superuser role. Values come from set_config(..., true).
CREATE POLICY hr_document_select_scope ON hr_document_chunks FOR SELECT TO peoplevault_app USING (
  document_type = 'hr_policy'
  OR (document_type IN ('payslip', 'tax_statement') AND owner_id = current_setting('app.user_id', true))
  OR current_setting('app.user_role', true) = 'hr_payroll'
  OR (document_type = 'manager_policy' AND current_setting('app.user_role', true) IN ('manager', 'hr_partner'))
);

CREATE POLICY hr_document_ingest_scope ON hr_document_chunks FOR INSERT TO peoplevault_app
  WITH CHECK (current_setting('app.user_role', true) = 'hr_payroll');

CREATE POLICY hr_document_update_scope ON hr_document_chunks FOR UPDATE TO peoplevault_app
  USING (current_setting('app.user_role', true) = 'hr_payroll')
  WITH CHECK (current_setting('app.user_role', true) = 'hr_payroll');

GRANT SELECT, INSERT, UPDATE ON hr_document_chunks TO peoplevault_app;

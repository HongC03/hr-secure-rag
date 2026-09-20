-- Add document-parent relationships for long-document RAG chunking.
-- Existing one-row records (for example payslips) become their own parent at index 0.
ALTER TABLE hr_document_chunks ADD COLUMN IF NOT EXISTS parent_document_id TEXT;
ALTER TABLE hr_document_chunks ADD COLUMN IF NOT EXISTS chunk_index INTEGER;

UPDATE hr_document_chunks
SET parent_document_id = document_id, chunk_index = 0
WHERE parent_document_id IS NULL OR chunk_index IS NULL;

ALTER TABLE hr_document_chunks ALTER COLUMN parent_document_id SET NOT NULL;
ALTER TABLE hr_document_chunks ALTER COLUMN chunk_index SET NOT NULL;
ALTER TABLE hr_document_chunks ALTER COLUMN chunk_index SET DEFAULT 0;
ALTER TABLE hr_document_chunks ADD CONSTRAINT hr_document_chunks_chunk_index_nonnegative CHECK (chunk_index >= 0);

CREATE INDEX IF NOT EXISTS hr_document_chunks_parent_chunk_idx ON hr_document_chunks (parent_document_id, chunk_index);

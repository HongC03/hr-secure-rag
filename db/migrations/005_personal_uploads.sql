-- Owner-only uploads use the existing persistent chunk store.
-- The privileged payroll policy does not grant access to personal uploads.
DROP POLICY IF EXISTS hr_document_select_scope ON hr_document_chunks;
CREATE POLICY hr_document_select_scope ON hr_document_chunks FOR SELECT TO peoplevault_app USING (
  (document_type = 'personal_upload'
    AND classification = 'PRIVATE · UPLOAD'
    AND owner_id = NULLIF(current_setting('app.user_id', true), ''))
  OR (document_type <> 'personal_upload' AND (
    document_type = 'hr_policy'
    OR (document_type IN ('payslip', 'tax_statement') AND owner_id = current_setting('app.user_id', true))
    OR current_setting('app.user_role', true) = 'hr_payroll'
    OR (document_type = 'manager_policy' AND current_setting('app.user_role', true) IN ('manager', 'hr_partner'))
  ))
);

DROP POLICY IF EXISTS hr_document_ingest_scope ON hr_document_chunks;
CREATE POLICY hr_document_ingest_scope ON hr_document_chunks FOR INSERT TO peoplevault_app WITH CHECK (
  (document_type = 'personal_upload'
    AND classification = 'PRIVATE · UPLOAD'
    AND owner_id = NULLIF(current_setting('app.user_id', true), ''))
  OR (document_type <> 'personal_upload' AND current_setting('app.user_role', true) = 'hr_payroll')
);

-- Existing uploads are immutable through the API; only synthetic records are updated.
DROP POLICY IF EXISTS hr_document_update_scope ON hr_document_chunks;
CREATE POLICY hr_document_update_scope ON hr_document_chunks FOR UPDATE TO peoplevault_app
  USING (document_type <> 'personal_upload' AND current_setting('app.user_role', true) = 'hr_payroll')
  WITH CHECK (document_type <> 'personal_upload' AND current_setting('app.user_role', true) = 'hr_payroll');

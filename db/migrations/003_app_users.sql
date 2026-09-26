-- Account passwords are stored only as hashes; no plaintext credentials are stored.
CREATE TABLE IF NOT EXISTS app_users (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('employee', 'manager', 'hr_payroll', 'hr_partner')),
  department TEXT NOT NULL,
  label TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

REVOKE ALL ON app_users FROM PUBLIC;
GRANT SELECT ON app_users TO peoplevault_app;

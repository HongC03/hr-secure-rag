-- Public registration uses a separate login namespace and a server-generated user ID.
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS login_name TEXT;
ALTER TABLE app_users ALTER COLUMN role SET DEFAULT 'employee';

CREATE UNIQUE INDEX IF NOT EXISTS app_users_login_name_uidx ON app_users (login_name)
  WHERE login_name IS NOT NULL;

-- The application can only insert unprivileged accounts. Administrators retain
-- responsibility for role changes and password resets through manage_user.py.
REVOKE INSERT, UPDATE, DELETE ON app_users FROM peoplevault_app;
GRANT INSERT (user_id, login_name, name, department, label, password_hash)
  ON app_users TO peoplevault_app;

ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_users FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS app_users_read ON app_users;
CREATE POLICY app_users_read ON app_users FOR SELECT TO peoplevault_app USING (true);

DROP POLICY IF EXISTS app_users_register ON app_users;
CREATE POLICY app_users_register ON app_users FOR INSERT TO peoplevault_app
  WITH CHECK (role = 'employee' AND login_name LIKE '@%');

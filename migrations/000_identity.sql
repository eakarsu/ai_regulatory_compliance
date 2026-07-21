BEGIN;
CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
DO $$ BEGIN
  CREATE TYPE userrole AS ENUM ('admin', 'analyst', 'viewer');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  organization TEXT,
  role userrole NOT NULL DEFAULT 'analyst',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  tenant_id TEXT,
  oidc_subject TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oidc_subject TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
INSERT INTO tenants(id, name)
SELECT 'tenant_' || id, COALESCE(NULLIF(organization, ''), 'Imported organization') FROM users
WHERE tenant_id IS NULL
ON CONFLICT (id) DO NOTHING;
UPDATE users SET tenant_id = 'tenant_' || id WHERE tenant_id IS NULL;
ALTER TABLE users ALTER COLUMN tenant_id SET NOT NULL;
DO $$ BEGIN
  ALTER TABLE users ADD CONSTRAINT users_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
CREATE INDEX IF NOT EXISTS users_tenant_id_idx ON users(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS users_oidc_subject_key ON users(oidc_subject) WHERE oidc_subject IS NOT NULL;
COMMIT;

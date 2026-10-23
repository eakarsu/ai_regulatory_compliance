-- Staff tasks for authenticated follow-ups. Apply through the normal migration path; not auto-applied.
CREATE TABLE IF NOT EXISTS staff_tasks (
  id VARCHAR PRIMARY KEY,
  tenant_id VARCHAR NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR NOT NULL,
  description TEXT,
  priority VARCHAR NOT NULL DEFAULT 'NORMAL',
  status VARCHAR NOT NULL DEFAULT 'OPEN',
  due_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_staff_tasks_tenant_id ON staff_tasks (tenant_id);
CREATE INDEX IF NOT EXISTS ix_staff_tasks_user_id ON staff_tasks (user_id);

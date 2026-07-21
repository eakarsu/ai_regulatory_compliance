import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from auth import hash_password
from database import SessionLocal
from models import Tenant, User, UserRole


if os.getenv("BOOTSTRAP_ACKNOWLEDGEMENT") != "create-initial-admin":
    raise RuntimeError("BOOTSTRAP_ACKNOWLEDGEMENT=create-initial-admin is required")

email = os.getenv("PROVISION_ADMIN_EMAIL", "").strip().lower()
password = os.getenv("PROVISION_ADMIN_PASSWORD", "")
name = os.getenv("PROVISION_ADMIN_NAME", "").strip()
company = os.getenv("PROVISION_COMPANY_NAME", "").strip()
tenant_id = os.getenv("GOVERNANCE_TENANT_ID", "").strip()
if "@" not in email or len(password) < 12 or not name or not company or not tenant_id:
    raise RuntimeError(
        "PROVISION_ADMIN_EMAIL, PROVISION_ADMIN_PASSWORD (12+ characters), "
        "PROVISION_ADMIN_NAME, PROVISION_COMPANY_NAME, and GOVERNANCE_TENANT_ID are required"
    )

database = SessionLocal()
try:
    existing = database.query(User).filter(User.email == email).first()
    if existing:
        print(json.dumps({"event": "initial_admin_exists", "user_id": existing.id}))
    else:
        tenant = database.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenant = Tenant(id=tenant_id, name=company)
            database.add(tenant)
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            organization=company,
            role=UserRole.admin,
            tenant_id=tenant_id,
            is_active=True,
        )
        database.add(user)
        database.commit()
        database.refresh(user)
        print(json.dumps({"event": "initial_admin_created", "user_id": user.id}))
finally:
    database.close()

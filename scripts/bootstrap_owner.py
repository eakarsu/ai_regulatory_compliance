import json
import os
import secrets
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import hash_password
from database import SessionLocal
from models import Tenant, User

if os.getenv("ALLOW_IDENTITY_BOOTSTRAP") != "1":
    raise RuntimeError("Set ALLOW_IDENTITY_BOOTSTRAP=1 for this one-time operation")
for key in ("TENANT_NAME", "OWNER_EMAIL", "OWNER_NAME", "OIDC_SUBJECT"):
    if not os.getenv(key):
        raise RuntimeError(f"{key} is required")

db = SessionLocal()
try:
    email, subject = os.environ["OWNER_EMAIL"].lower(), os.environ["OIDC_SUBJECT"]
    if db.query(User).filter((User.email == email) | (User.oidc_subject == subject)).first():
        raise RuntimeError("Owner email or OIDC subject is already provisioned")
    tenant = Tenant(id=f"tenant_{uuid.uuid4().hex}", name=os.environ["TENANT_NAME"])
    user = User(email=email, name=os.environ["OWNER_NAME"], organization=tenant.name, role="admin", tenant_id=tenant.id,
                oidc_subject=subject, password_hash=hash_password(secrets.token_urlsafe(32)))
    db.add_all([tenant, user]); db.commit(); db.refresh(user)
    print(json.dumps({"event": "tenant_owner_bootstrapped", "tenant_id": tenant.id, "user_id": user.id, "email": user.email}))
finally:
    db.close()

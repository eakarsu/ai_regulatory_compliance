# Environment contract

Always required: `DATABASE_URL`. Local/test authentication additionally requires `AUTH_MODE=local` and a random `JWT_SECRET` of at least 32 characters. Production requires `ENVIRONMENT=production`, `AUTH_MODE=oidc`, `OIDC_ISSUER`, `OIDC_AUDIENCE`, and `OIDC_JWKS_URL`; local login/registration are disabled. Set the exact `CLIENT_URL` and enable `ENABLE_SCHEDULER=true` on only one elected worker.

`ENABLE_LEGACY_ROUTES=true` and frontend `VITE_ENABLE_LEGACY_UI=true` are permitted only outside production and expose historic, generic-AI, and generated prototype surfaces. AI/provider credentials are optional and absent from the authoritative workflow. `ALLOW_SCHEMA_MIGRATION=1` and `ALLOW_DATABASE_RESTORE=1` acknowledge one explicit operation. Store secrets and connector credentials in a production secret manager.

For a new production tenant, run `python scripts/bootstrap_owner.py` once with `ALLOW_IDENTITY_BOOTSTRAP=1`, `TENANT_NAME`, `OWNER_EMAIL`, `OWNER_NAME`, and the verified `OIDC_SUBJECT`. Remove the acknowledgement immediately afterward.

BEGIN;
CREATE OR REPLACE FUNCTION immutable_governance_evidence() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'governance evidence is append-only';END$$;
DROP TRIGGER IF EXISTS regulatory_source_versions_immutable ON regulatory_source_versions;
CREATE TRIGGER regulatory_source_versions_immutable BEFORE UPDATE OR DELETE ON regulatory_source_versions FOR EACH ROW EXECUTE FUNCTION immutable_governance_evidence();
DROP TRIGGER IF EXISTS governed_evidence_links_immutable ON governed_evidence_links;
CREATE TRIGGER governed_evidence_links_immutable BEFORE UPDATE OR DELETE ON governed_evidence_links FOR EACH ROW EXECUTE FUNCTION immutable_governance_evidence();
DROP TRIGGER IF EXISTS governed_evaluations_immutable ON governed_evaluations;
CREATE TRIGGER governed_evaluations_immutable BEFORE UPDATE OR DELETE ON governed_evaluations FOR EACH ROW EXECUTE FUNCTION immutable_governance_evidence();

CREATE OR REPLACE FUNCTION protect_policy_version_fields() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.tenant_id <> OLD.tenant_id OR NEW.policy_key <> OLD.policy_key OR NEW.version <> OLD.version OR NEW.owner_id <> OLD.owner_id OR NEW.body_digest <> OLD.body_digest OR NEW.created_at <> OLD.created_at THEN
    RAISE EXCEPTION 'versioned policy content and ownership are immutable';
  END IF;
  IF OLD.legal_hold AND NOT NEW.legal_hold THEN RAISE EXCEPTION 'legal hold release requires a dedicated legal procedure'; END IF;
  IF OLD.retain_until IS NOT NULL AND (NEW.retain_until IS NULL OR NEW.retain_until < OLD.retain_until) THEN RAISE EXCEPTION 'retention cannot be shortened'; END IF;
  RETURN NEW;
END$$;
DROP TRIGGER IF EXISTS governed_policy_version_fields ON governed_policy_versions;
CREATE TRIGGER governed_policy_version_fields BEFORE UPDATE ON governed_policy_versions FOR EACH ROW EXECUTE FUNCTION protect_policy_version_fields();

CREATE INDEX IF NOT EXISTS regulatory_source_lookup ON regulatory_source_versions(tenant_id, source_uri, retrieved_at DESC);
CREATE INDEX IF NOT EXISTS governed_decision_export ON governed_decisions(tenant_id, occurred_at, id);
COMMIT;

"""Deterministic offline insights over governed policy records.

Never calls a provider; every result is labelled aiGenerated=False.
"""
from datetime import datetime, timezone

DISCLAIMER = "Deterministic summary computed locally from the governed record; it is not AI-generated. Validate before acting."


def _labelled(summary, sections):
    return {"aiGenerated": False, "source": "deterministic-fallback", "summary": summary,
            "sections": sections, "disclaimer": DISCLAIMER}


def obligation_coverage(policy, evidence):
    owners = {item.get("owner_id") for item in evidence if item.get("owner_id")}
    return _labelled(
        f"Policy {policy.get('policy_key')} v{policy.get('version')} has {len(evidence)} cited obligations across {len(owners)} owners.",
        [
            {"title": "Cited obligations", "detail": len(evidence)},
            {"title": "Distinct owners", "detail": len(owners)},
            {"title": "Legal hold", "detail": bool(policy.get("legal_hold"))},
        ],
    )


def risk_summary(policy, evidence):
    counts = {}
    for item in evidence:
        rating = item.get("risk_rating") or "unknown"
        counts[rating] = counts.get(rating, 0) + 1
    high = counts.get("high", 0) + counts.get("critical", 0)
    return _labelled(
        f"{high} of {len(evidence)} obligations are rated high or critical for {policy.get('policy_key')}.",
        [
            {"title": "Obligations by risk rating", "detail": counts},
            {"title": "High or critical", "detail": high},
            {"title": "Policy status", "detail": policy.get("status")},
        ],
    )


def deadline_outlook(policy, evidence, now=None):
    now = now or datetime.now(timezone.utc)
    dated = []
    for item in evidence:
        raw = item.get("deadline")
        if not raw:
            continue
        try:
            when = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        dated.append((when, item))
    dated.sort(key=lambda pair: pair[0])
    overdue = [item for when, item in dated if when < now]
    next_due = dated[0][0].date().isoformat() if dated else None
    return _labelled(
        f"{len(overdue)} obligations are past their deadline; next due: {next_due or 'none recorded'}.",
        [
            {"title": "Overdue obligations", "detail": len(overdue)},
            {"title": "Next deadline", "detail": next_due},
            {"title": "Dated obligations", "detail": len(dated)},
        ],
    )


INSIGHTS = {"coverage": obligation_coverage, "risk": risk_summary, "deadlines": deadline_outlook}

"""APScheduler background jobs for compliance monitoring."""
import json
import os
from datetime import datetime, timedelta

import anthropic
from apscheduler.schedulers.background import BackgroundScheduler

from database import SessionLocal
from models import (
    AIAnalysisLog, ComplianceAlert, ComplianceAssessment,
    AlertSeverity, Regulation, User,
)

scheduler = BackgroundScheduler(timezone="UTC")
MODEL = "claude-3-5-sonnet-20241022"


def parse_ai_json(text: str):
    """Robust multi-strategy JSON extraction."""
    try:
        return json.loads(text)
    except Exception:
        pass
    stripped = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(stripped)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    return None


def check_upcoming_reviews() -> None:
    """Daily job: create alerts for assessments with next_review_date within 30 days (idempotent)."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")
        cutoff = now + timedelta(days=30)

        assessments = (
            db.query(ComplianceAssessment)
            .filter(
                ComplianceAssessment.next_review_date != None,
                ComplianceAssessment.next_review_date >= now,
                ComplianceAssessment.next_review_date <= cutoff,
            )
            .all()
        )

        alert_count = 0
        for assessment in assessments:
            days_left = (assessment.next_review_date - now).days
            severity = AlertSeverity.critical if days_left <= 7 else AlertSeverity.warning

            dedup_key = f"scheduler:upcoming_review:{assessment.id}:{today_str}"
            existing = db.query(ComplianceAlert).filter(
                ComplianceAlert.dedup_key == dedup_key
            ).first()
            if existing:
                continue

            reg = db.query(Regulation).filter(Regulation.id == assessment.regulation_id).first()
            reg_name = reg.title if reg else "Unknown Regulation"

            alert = ComplianceAlert(
                user_id=assessment.user_id,
                regulation_id=assessment.regulation_id,
                alert_type="upcoming_review",
                severity=severity,
                message=(
                    f"[{reg_name}] Compliance review due in {days_left} day(s) "
                    f"on {assessment.next_review_date.strftime('%Y-%m-%d')}. "
                    f"Current score: {assessment.overall_score}/100."
                ),
                dedup_key=dedup_key,
            )
            db.add(alert)
            alert_count += 1

        db.commit()
        print(f"[Scheduler] check_upcoming_reviews: created {alert_count} alert(s) at {now.isoformat()}")
    except Exception as e:
        print(f"[Scheduler] check_upcoming_reviews error: {e}")
    finally:
        db.close()


def weekly_ai_compliance_summary() -> None:
    """Weekly job: run AI compliance summary for all active users with assessments."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[Scheduler] ANTHROPIC_API_KEY not set, skipping weekly summary")
        return

    db = SessionLocal()
    try:
        users = db.query(User).all()
        client = anthropic.Anthropic(api_key=api_key)

        for user in users:
            assessments = (
                db.query(ComplianceAssessment)
                .filter(ComplianceAssessment.user_id == user.id)
                .all()
            )
            if not assessments:
                continue

            summary_data = []
            for a in assessments:
                reg = db.query(Regulation).filter(Regulation.id == a.regulation_id).first()
                summary_data.append({
                    "regulation": reg.title if reg else a.regulation_id,
                    "category": reg.category if reg else "Unknown",
                    "score": a.overall_score,
                    "status": a.status,
                    "findings_count": len(a.findings or []),
                    "next_review": a.next_review_date.isoformat() if a.next_review_date else None,
                })

            prompt = f"""Provide a weekly compliance summary for an organization with {len(assessments)} assessments.
Assessment data:
{json.dumps(summary_data, indent=2)}

Return ONLY valid JSON:
{{
  "overall_posture": "good|fair|poor",
  "posture_score": 0,
  "headline": "one sentence summary",
  "key_risks": ["top 3 risks requiring attention"],
  "improvements_this_week": ["positive developments"],
  "action_items": ["top 5 prioritized action items"],
  "regulations_requiring_attention": ["list of regulation names needing immediate focus"],
  "weeks_outlook": "brief outlook for the coming week"
}}"""

            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=1000,
                    system="You are a compliance monitoring system generating weekly executive summaries.",
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text
                result = parse_ai_json(content)
                if result is None:
                    result = {"raw_response": content, "parse_error": True}
                tokens = response.usage.input_tokens + response.usage.output_tokens
            except Exception as ai_err:
                print(f"[Scheduler] AI error for user {user.id}: {ai_err}")
                continue

            db.add(AIAnalysisLog(
                user_id=user.id,
                analysis_type="weekly_compliance_summary",
                input_summary=f"Weekly summary for {user.email} ({len(assessments)} assessments)",
                result=result,
                tokens_used=tokens,
            ))

        db.commit()
        print(f"[Scheduler] weekly_ai_compliance_summary completed at {datetime.utcnow().isoformat()}")
    except Exception as e:
        print(f"[Scheduler] weekly_ai_compliance_summary error: {e}")
    finally:
        db.close()


def check_overdue_assessments() -> None:
    """Daily job: create critical alerts for non-compliant assessments."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")

        non_compliant = (
            db.query(ComplianceAssessment)
            .filter(ComplianceAssessment.status == "non_compliant")
            .all()
        )

        alert_count = 0
        for assessment in non_compliant:
            dedup_key = f"scheduler:non_compliant:{assessment.id}:{today_str}"
            existing = db.query(ComplianceAlert).filter(
                ComplianceAlert.dedup_key == dedup_key
            ).first()
            if existing:
                continue

            reg = db.query(Regulation).filter(Regulation.id == assessment.regulation_id).first()
            reg_name = reg.title if reg else "Unknown Regulation"

            alert = ComplianceAlert(
                user_id=assessment.user_id,
                regulation_id=assessment.regulation_id,
                alert_type="non_compliant_status",
                severity=AlertSeverity.critical,
                message=(
                    f"[{reg_name}] Assessment is non-compliant (score: {assessment.overall_score}/100). "
                    f"Immediate remediation required."
                ),
                dedup_key=dedup_key,
            )
            db.add(alert)
            alert_count += 1

        db.commit()
        print(f"[Scheduler] check_overdue_assessments: created {alert_count} alert(s)")
    except Exception as e:
        print(f"[Scheduler] check_overdue_assessments error: {e}")
    finally:
        db.close()


def start_scheduler() -> None:
    # Daily at 08:00 UTC — upcoming reviews
    scheduler.add_job(
        check_upcoming_reviews,
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_review_check",
        replace_existing=True,
    )

    # Daily at 08:30 UTC — non-compliant alerts
    scheduler.add_job(
        check_overdue_assessments,
        trigger="cron",
        hour=8,
        minute=30,
        id="daily_overdue_check",
        replace_existing=True,
    )

    # Weekly on Monday at 09:00 UTC
    scheduler.add_job(
        weekly_ai_compliance_summary,
        trigger="cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        id="weekly_ai_summary",
        replace_existing=True,
    )

    scheduler.start()
    print(
        "[Scheduler] Started. Jobs: "
        "daily_review_check (08:00 UTC), "
        "daily_overdue_check (08:30 UTC), "
        "weekly_ai_summary (Mon 09:00 UTC)"
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] Stopped.")

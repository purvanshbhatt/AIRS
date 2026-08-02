"""
V2 Morning Check Generator — Real telemetry, real moments.

Consumes the V2 ClinicEvaluationEngine and produces the Morning Safety Check
that clinic owners receive every morning.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from app.services.clinic_engine.v2.schema import ClinicMoment, Verdict


class QuestionSummary(BaseModel):
    """Summary of how one customer question was answered."""
    question_id: str
    question_text: str
    status: str  # "safe", "concern", "critical"
    moment_count: int


class MorningCheckV2(BaseModel):
    """The Morning Safety Check a clinic owner sees."""
    id: str
    date: str
    status: str  # "ALL_CLEAR" or "NEEDS_ATTENTION"
    headline: str  # One-sentence summary for the clinic owner
    moments: List[ClinicMoment] = Field(default_factory=list)
    questions_answered: List[QuestionSummary] = Field(default_factory=list)
    generated_at: str


class MorningCheckGeneratorV2:
    """Generates the Morning Safety Check from V2 ClinicMoments."""

    # The three customer questions
    QUESTIONS = {
        "Q1": "Does someone who shouldn't have access still have access?",
        "Q2": "Can I recover my clinic today if systems fail?",
        "Q3": "Is one of my devices likely to be compromised?",
    }

    def generate(self, moments: List[ClinicMoment]) -> MorningCheckV2:
        """Build the morning check from evaluated moments."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        # Determine overall status
        has_critical = any(m.verdict == Verdict.CRITICAL for m in moments)
        has_concern = any(m.verdict == Verdict.CONCERN for m in moments)
        status = "NEEDS_ATTENTION" if (has_critical or has_concern) else "ALL_CLEAR"

        # Build headline
        if has_critical:
            critical_count = sum(1 for m in moments if m.verdict == Verdict.CRITICAL)
            headline = (
                f"{critical_count} urgent {'issue needs' if critical_count == 1 else 'issues need'} "
                f"your attention before seeing patients today."
            )
        elif has_concern:
            concern_count = sum(1 for m in moments if m.verdict == Verdict.CONCERN)
            headline = (
                f"{concern_count} {'item' if concern_count == 1 else 'items'} to be aware of, "
                f"but nothing blocking your day."
            )
        else:
            headline = "Everything looks good. Your clinic is ready for patients."

        # Summarize each question
        question_summaries = []
        for qid, qtext in self.QUESTIONS.items():
            q_moments = [m for m in moments if m.question_id == qid]
            if any(m.verdict == Verdict.CRITICAL for m in q_moments):
                q_status = "critical"
            elif any(m.verdict == Verdict.CONCERN for m in q_moments):
                q_status = "concern"
            else:
                q_status = "safe"

            question_summaries.append(QuestionSummary(
                question_id=qid,
                question_text=qtext,
                status=q_status,
                moment_count=len(q_moments),
            ))

        return MorningCheckV2(
            id=f"mc-{date_str}",
            date=date_str,
            status=status,
            headline=headline,
            moments=moments,
            questions_answered=question_summaries,
            generated_at=now.isoformat(),
        )

"""NL → structured catalog filters. Heuristic compiler so tests need no LLM."""

from __future__ import annotations

from dataclasses import dataclass

from .templates import (
    COMPETITIVE_BRIEF,
    EMAIL_VERIFY,
    ICP_FIT,
    LEAD_ENRICHMENT,
    RESUME_SCREEN,
)


@dataclass(frozen=True)
class CompiledSearch:
    template_id: str | None
    sla_only: bool
    certified_or_better: bool
    max_credits_per_row: int | None
    min_eval: float | None
    explanation: str


_TEMPLATE_HINTS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (EMAIL_VERIFY, ("bounce", "deliverability", "verify email", "email verify", "mailbox"), "email verify"),
    (ICP_FIT, ("icp", "fit score", "ideal customer"), "ICP fit"),
    (COMPETITIVE_BRIEF, ("competitor", "competitive", "cite", "research brief"), "competitive brief"),
    (RESUME_SCREEN, ("resume", "recruiter", "screen candidate", "hiring screen"), "resume screen"),
    (LEAD_ENRICHMENT, ("enrich", "lead", "sdr", "founder", "ecommerce", "domain"), "lead enrichment"),
)


def compile_search_query(text: str) -> CompiledSearch:
    q = text.lower()
    bits: list[str] = []

    template_id = None
    for tid, words, label in _TEMPLATE_HINTS:
        if any(w in q for w in words):
            template_id = tid
            bits.append(f"{label} template")
            break
    if template_id is None:
        bits.append("all live specializations")

    sla_only = any(w in q for w in ("hire", "retainer", "sla", "on staff"))
    if sla_only:
        bits.append("SLA/Hire only")

    certified_or_better = "certified" in q or "trusted" in q or sla_only
    if certified_or_better and not sla_only:
        bits.append("Certified or SLA")

    max_credits = None
    if any(w in q for w in ("cheap", "budget", "inexpensive", "under")):
        max_credits = 15
        bits.append("max 15 credits/row")

    min_eval = 0.85 if any(w in q for w in ("reliable", "accurate", "high eval")) else None
    if min_eval:
        bits.append(f"min eval {min_eval:.0%}")

    return CompiledSearch(
        template_id=template_id,
        sla_only=sla_only,
        certified_or_better=certified_or_better,
        max_credits_per_row=max_credits,
        min_eval=min_eval,
        explanation="; ".join(bits),
    )

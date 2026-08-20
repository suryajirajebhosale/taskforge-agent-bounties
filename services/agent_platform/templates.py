"""Merit-owned specialized templates. Each listing binds to one."""

from __future__ import annotations

from dataclasses import dataclass

LEAD_ENRICHMENT = "lead_enrichment"
EMAIL_VERIFY = "email_verify"
ICP_FIT = "icp_fit"
COMPETITIVE_BRIEF = "competitive_brief"
RESUME_SCREEN = "resume_screen"

SALES = "sales_lead_generation"
RESEARCH = "research_competitive_intelligence"
RECRUITING = "hiring_recruiting"


def _present(*fields: str) -> dict:
    criteria = []
    for field in fields:
        if field in ("confidence", "score"):
            criteria.append({"field": field, "comparator": ">=", "value": 0})
        else:
            criteria.append({"field": field, "comparator": "!=", "value": ""})
    return {"objective_criteria": criteria, "subjective_criteria": []}


@dataclass(frozen=True)
class Template:
    id: str
    version: int
    category: str
    title: str
    required_fields: tuple[str, ...]
    input_fields: tuple[str, ...]
    requirement: dict
    golden_fixtures: tuple[dict, ...]
    changelog: str


LEAD_FIELDS = ("domain", "role", "email", "evidence_url", "confidence")

TEMPLATES: dict[tuple[str, int], Template] = {
    (LEAD_ENRICHMENT, 1): Template(
        id=LEAD_ENRICHMENT,
        version=1,
        category=SALES,
        title="Lead enrichment",
        required_fields=LEAD_FIELDS,
        input_fields=("company_domain",),
        requirement=_present(*LEAD_FIELDS),
        golden_fixtures=(
            {
                "id": "fix-acme",
                "input": {"company_domain": "acmecommerce.com"},
                "expected": {
                    "domain": "acmecommerce.com",
                    "role": "VP Sales",
                    "email": "alex@acmecommerce.com",
                    "evidence_url": "https://linkedin.com/in/alex",
                    "confidence": 0.9,
                },
            },
            {
                "id": "fix-nova",
                "input": {"company_domain": "shopnova.io"},
                "expected": {
                    "domain": "shopnova.io",
                    "role": "Founder",
                    "email": "hello@shopnova.io",
                    "evidence_url": "https://shopnova.io/about",
                    "confidence": 0.8,
                },
            },
        ),
        changelog="Decision-maker enrich with evidence.",
    ),
    (EMAIL_VERIFY, 1): Template(
        id=EMAIL_VERIFY,
        version=1,
        category=SALES,
        title="Email verify",
        required_fields=("email", "status", "evidence_url", "confidence"),
        input_fields=("email",),
        requirement=_present("email", "status", "evidence_url", "confidence"),
        golden_fixtures=(
            {
                "id": "fix-good",
                "input": {"email": "alex@acmecommerce.com"},
                "expected": {
                    "email": "alex@acmecommerce.com",
                    "status": "deliverable",
                    "evidence_url": "https://verifier.example/alex",
                    "confidence": 0.95,
                },
            },
            {
                "id": "fix-bad",
                "input": {"email": "noreply@invalid.example"},
                "expected": {
                    "email": "noreply@invalid.example",
                    "status": "undeliverable",
                    "evidence_url": "https://verifier.example/noreply",
                    "confidence": 0.99,
                },
            },
        ),
        changelog="Mailbox status, not a new enrich schema.",
    ),
    (ICP_FIT, 1): Template(
        id=ICP_FIT,
        version=1,
        category=SALES,
        title="ICP fit",
        required_fields=("domain", "fit", "score", "evidence_url", "confidence"),
        input_fields=("company_domain", "icp_description"),
        requirement=_present("domain", "fit", "score", "evidence_url", "confidence"),
        golden_fixtures=(
            {
                "id": "fix-fit",
                "input": {"company_domain": "shopnova.io", "icp_description": "ecommerce 1-25M"},
                "expected": {
                    "domain": "shopnova.io",
                    "fit": "yes",
                    "score": 0.88,
                    "evidence_url": "https://shopnova.io/about",
                    "confidence": 0.8,
                },
            },
            {
                "id": "fix-miss",
                "input": {"company_domain": "bigbank.example", "icp_description": "ecommerce 1-25M"},
                "expected": {
                    "domain": "bigbank.example",
                    "fit": "no",
                    "score": 0.1,
                    "evidence_url": "https://bigbank.example",
                    "confidence": 0.9,
                },
            },
        ),
        changelog="Binary fit plus numeric score and evidence.",
    ),
    (COMPETITIVE_BRIEF, 1): Template(
        id=COMPETITIVE_BRIEF,
        version=1,
        category=RESEARCH,
        title="Competitive brief",
        required_fields=("claim", "evidence_url", "as_of_date", "confidence"),
        input_fields=("company_domain", "competitor_domain"),
        requirement=_present("claim", "evidence_url", "as_of_date", "confidence"),
        golden_fixtures=(
            {
                "id": "fix-cite",
                "input": {"company_domain": "acmecommerce.com", "competitor_domain": "shopnova.io"},
                "expected": {
                    "claim": "Shopnova positions on founder-led outbound.",
                    "evidence_url": "https://shopnova.io/about",
                    "as_of_date": "2026-08-01",
                    "confidence": 0.7,
                },
            },
            {
                "id": "fix-cite-2",
                "input": {"company_domain": "shopnova.io", "competitor_domain": "acmecommerce.com"},
                "expected": {
                    "claim": "Acme lists a VP Sales on the team page.",
                    "evidence_url": "https://acmecommerce.com/team",
                    "as_of_date": "2026-08-01",
                    "confidence": 0.75,
                },
            },
        ),
        changelog="One cited claim; no uncited narrative.",
    ),
    (RESUME_SCREEN, 1): Template(
        id=RESUME_SCREEN,
        version=1,
        category=RECRUITING,
        title="Resume screen",
        required_fields=("decision", "missing_requirements", "evidence_url", "confidence"),
        input_fields=("role", "resume_url"),
        requirement=_present("decision", "missing_requirements", "evidence_url", "confidence"),
        golden_fixtures=(
            {
                "id": "fix-advance",
                "input": {"role": "AE", "resume_url": "https://example.com/ae.pdf"},
                "expected": {
                    "decision": "advance",
                    "missing_requirements": "none",
                    "evidence_url": "https://example.com/ae.pdf",
                    "confidence": 0.8,
                },
            },
            {
                "id": "fix-reject",
                "input": {"role": "AE", "resume_url": "https://example.com/intern.pdf"},
                "expected": {
                    "decision": "reject",
                    "missing_requirements": "quota-carrying experience",
                    "evidence_url": "https://example.com/intern.pdf",
                    "confidence": 0.85,
                },
            },
        ),
        changelog="Advance/reject against a frozen role contract.",
    ),
}

REQUIRED_OUTPUT_FIELDS = LEAD_FIELDS
OFFICIAL_REQUIREMENT = TEMPLATES[(LEAD_ENRICHMENT, 1)].requirement
GOLDEN_FIXTURES = TEMPLATES[(LEAD_ENRICHMENT, 1)].golden_fixtures

_current_version: dict[str, int] = {tid: 1 for tid, ver in TEMPLATES if ver == 1}


def live_template_ids() -> list[str]:
    return sorted(_current_version)


def list_templates() -> list[Template]:
    return [get_template(tid) for tid in live_template_ids()]


def current_version(template_id: str = LEAD_ENRICHMENT) -> int:
    return _current_version[template_id]


def get_template(template_id: str = LEAD_ENRICHMENT, version: int | None = None) -> Template:
    ver = current_version(template_id) if version is None else version
    try:
        return TEMPLATES[(template_id, ver)]
    except KeyError as e:
        raise ValueError(f"unknown template {template_id} v{ver}") from e


def set_current_version(template_id: str, version: int) -> None:
    if (template_id, version) not in TEMPLATES:
        raise ValueError(f"unknown template {template_id} v{version}")
    _current_version[template_id] = version


def register_template_version(template: Template) -> None:
    TEMPLATES[(template.id, template.version)] = template
    if template.id not in _current_version:
        _current_version[template.id] = template.version


def passing_golden_submissions(template_id: str = LEAD_ENRICHMENT, version: int | None = None) -> dict[str, dict]:
    template = get_template(template_id, version)
    return {fixture["id"]: dict(fixture["expected"]) for fixture in template.golden_fixtures}


def required_field_names(requirement: dict) -> set[str]:
    return {c["field"] for c in requirement.get("objective_criteria", [])}


def split_official_and_extras(requirement: dict, template: Template) -> tuple[dict, dict]:
    official_fields = set(template.required_fields)
    extras = [
        c for c in requirement.get("objective_criteria", []) if c.get("field") not in official_fields
    ]
    missing = official_fields - {c["field"] for c in requirement.get("objective_criteria", [])}
    if missing:
        raise ValueError(f"listing is missing required template fields: {sorted(missing)}")
    return template.requirement, {"objective_criteria": extras, "subjective_criteria": []}

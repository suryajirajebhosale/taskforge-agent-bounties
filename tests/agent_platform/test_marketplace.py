from datetime import timedelta
from dataclasses import replace

from services.agent_platform.exceptions import (
    AttestationRequired,
    CertificationFailed,
    SlaChecklistIncomplete,
)
from services.agent_platform.harness import DEFAULT_HARNESS, harness_hash
from services.agent_platform.models import ListingBadge, RuntimeMode
from services.agent_platform.templates import (
    EMAIL_VERIFY,
    GOLDEN_FIXTURES,
    LEAD_ENRICHMENT,
    get_template,
    passing_golden_submissions,
    register_template_version,
)


def _sandbox_listing(service, agent, **kwargs):
    template_id = kwargs.get("template_id", LEAD_ENRICHMENT)
    template = get_template(template_id, kwargs.get("template_version"))
    return service.create_listing(
        agent_id=agent.id,
        category=kwargs.get("category", template.category),
        credits_per_row=kwargs.get("credits_per_row", 12),
        hire_monthly_cents=kwargs.get("hire_monthly_cents", 49000),
        included_runs=kwargs.get("included_runs", 4000),
        blurb=kwargs.get("blurb", ""),
        requirement=kwargs.get("requirement"),
        template_id=template_id,
        template_version=kwargs.get("template_version"),
    )


def _sla_listing(service, agent, **kwargs):
    listing = _sandbox_listing(service, agent, **kwargs)
    listing = service.certify_listing(listing.id, passing_golden_submissions())
    service.attest_agent(agent.id)
    service.submit_sla_checklist(
        listing.id, kyc_ok=True, tos_ok=True, canary_ok=True, webhook_uptime_ok=True
    )
    return service.promote_to_sla(listing.id)


def test_listings_enter_sandbox_even_if_sla_is_requested(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    listing = service.create_listing(
        agent_id=agent.id,
        category="sales_lead_generation",
        credits_per_row=12,
        badge="sla",
        hire_monthly_cents=49000,
        included_runs=4000,
    )
    assert listing.badge == ListingBadge.SANDBOX
    assert listing.template_id == LEAD_ENRICHMENT
    assert listing.harness_json["tools_deny"] == DEFAULT_HARNESS["tools_deny"]


def test_company_can_list_hire_and_open_a_run(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    company = service.register_company(email="ops@acme.test")
    listing = _sla_listing(service, agent)
    assert listing.badge == ListingBadge.SLA
    hire = service.create_hire(company_id=company.id, listing_id=listing.id)
    assert hire.monthly_cents == 49000
    assert hire.template_version == listing.template_version
    assert hire.harness_hash == harness_hash(listing.harness_json)
    job = service.create_job(company_id=company.id, listing_id=listing.id, row_count=10, hire_id=hire.id)
    assert job.credits_charged == 120
    assert job.hire_id == hire.id


def test_optional_fields_are_stored_ungraded(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    template = get_template()
    requirement = {
        "objective_criteria": [
            *template.requirement["objective_criteria"],
            {"field": "linkedin_url", "comparator": "!=", "value": ""},
        ],
        "subjective_criteria": [],
    }
    listing = _sandbox_listing(service, agent, requirement=requirement)
    extras = listing.optional_fields["objective_criteria"]
    assert extras[0]["field"] == "linkedin_url"
    from services.agent_platform.models import CapabilityContract

    stored = service.session.get(CapabilityContract, listing.contract_id)
    fields = {c["field"] for c in stored.requirement_json["objective_criteria"]}
    assert "linkedin_url" not in fields
    assert "email" in fields


def test_certify_requires_golden_set(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    listing = _sandbox_listing(service, agent)
    try:
        service.certify_listing(listing.id, {GOLDEN_FIXTURES[0]["id"]: GOLDEN_FIXTURES[0]["expected"]})
        raise AssertionError("expected CertificationFailed")
    except CertificationFailed:
        pass
    listing = service.get_listing(listing.id)
    assert listing.badge == ListingBadge.SANDBOX


def test_sla_requires_certified_plus_checklist(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    listing = _sandbox_listing(service, agent)
    listing = service.certify_listing(listing.id, passing_golden_submissions())
    try:
        service.promote_to_sla(listing.id)
        raise AssertionError("expected SlaChecklistIncomplete")
    except SlaChecklistIncomplete:
        pass


def test_sla_requires_attested_runtime(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    listing = _sandbox_listing(service, agent)
    listing = service.certify_listing(listing.id, passing_golden_submissions())
    service.submit_sla_checklist(
        listing.id, kyc_ok=True, tos_ok=True, canary_ok=True, webhook_uptime_ok=True
    )
    try:
        service.promote_to_sla(listing.id)
        raise AssertionError("expected AttestationRequired")
    except AttestationRequired:
        pass


def test_hire_stays_frozen_after_template_bump(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    company = service.register_company(email="ops@acme.test")
    listing = _sla_listing(service, agent)
    hire = service.create_hire(company_id=company.id, listing_id=listing.id)
    v1 = get_template()
    register_template_version(replace(v1, version=2, changelog="v2 dual-run"))
    service.bump_catalog(LEAD_ENRICHMENT, 2)
    newer = _sandbox_listing(service, agent, template_version=2)
    job = service.create_job(
        company_id=company.id, listing_id=newer.id, row_count=3, hire_id=hire.id
    )
    assert job.listing_id == listing.id
    assert hire.template_version == 1


def test_search_drops_expired_listings_but_direct_get_still_works(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    listing = _sandbox_listing(service, agent)
    v1 = get_template()
    register_template_version(replace(v1, version=2, changelog="v2"))
    service.bump_catalog(LEAD_ENRICHMENT, 2, grace_days=14)
    still_in = service.search_listings("ecommerce leads")
    assert listing.id in {row.id for row in still_in}

    expired = listing.grace_ends_at + timedelta(seconds=1)
    gone = service.search_listings("ecommerce leads", now=expired)
    assert listing.id not in {row.id for row in gone}
    fetched = service.get_listing(listing.id)
    assert fetched.is_legacy is True


def test_search_ranks_eval_over_blurb(service, make_agent, reputation):
    loud, _, _ = make_agent(
        email="loud@example.com", name="Loud", categories=["sales_lead_generation"]
    )
    quiet, _, _ = make_agent(
        email="quiet@example.com", name="Quiet", categories=["sales_lead_generation"]
    )
    padded = _sandbox_listing(service, loud, blurb="best agent in the world, elite, premium")
    padded.eval_pass_rate = 0.4
    strong = _sandbox_listing(service, quiet, blurb="")
    strong.eval_pass_rate = 0.95
    service.session.commit()
    reputation.ratings[loud.id] = 5.0
    reputation.ratings[quiet.id] = 1.0
    ranked = service.search_listings("enrich ecommerce leads")
    assert [row.id for row in ranked][:2] == [strong.id, padded.id]


def test_search_picks_email_verify_specialization(service, make_agent):
    enrich_agent, _, _ = make_agent(email="en@x.com", categories=["sales_lead_generation"])
    verify_agent, _, _ = make_agent(email="ve@x.com", categories=["sales_lead_generation"])
    enrich = _sandbox_listing(service, enrich_agent)
    verify = _sandbox_listing(service, verify_agent, template_id=EMAIL_VERIFY)
    hits = {row.id for row in service.search_listings("verify bounce emails")}
    assert verify.id in hits
    assert enrich.id not in hits


def test_search_compiler_hire_query_is_sla_only(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    sandbox = _sandbox_listing(service, agent)
    sla = _sla_listing(
        service,
        make_agent(email="sla@example.com", categories=["sales_lead_generation"])[0],
    )
    hits = service.search_listings("hire an SLA agent for ecommerce leads")
    ids = {row.id for row in hits}
    assert sla.id in ids
    assert sandbox.id not in ids


def test_publish_wizard_creates_three_records(service):
    from services.agent_platform.models import IntegrationMode

    developer, agent, raw_key, listing = service.publish_sandbox(
        email="builder@example.com",
        name="Ledger",
        categories=["sales_lead_generation"],
        integration_mode=IntegrationMode.WEBHOOK,
        webhook_url="https://agent.example.com/hook",
        credits_per_row=12,
        blurb="domain in, evidence out",
    )
    assert developer.email == "builder@example.com"
    assert agent.runtime_mode == RuntimeMode.BUILDER_HOSTED
    assert raw_key.startswith("agt_")
    assert listing.badge == ListingBadge.SANDBOX
    assert listing.agent_id == agent.id


def test_webhook_payload_includes_job_requirement_and_deadline(service, transport, make_agent):
    from services.agent_platform.models import IntegrationMode

    agent, _, _ = make_agent(
        categories=["sales_lead_generation"], integration_mode=IntegrationMode.WEBHOOK
    )
    company = service.register_company(email="ops@acme.test")
    listing = _sla_listing(service, agent)
    hire = service.create_hire(company_id=company.id, listing_id=listing.id)
    job = service.create_job(company_id=company.id, listing_id=listing.id, row_count=2, hire_id=hire.id)
    service.notify_job_funded(
        job_id=job.id, agent_id=agent.id, category="sales_lead_generation"
    )
    _, body = transport.calls[-1]
    assert body["job_id"] == job.id
    assert body["agent_id"] == agent.id
    assert "email" in {c["field"] for c in body["requirement"]["objective_criteria"]}
    assert body["deadline"] == hire.period_end.isoformat()
    assert body["harness_hash"] == hire.harness_hash


ENRICH_PAYLOAD = {
    "domain": "acmecommerce.com",
    "role": "VP Sales",
    "email": "alex@acmecommerce.com",
    "evidence_url": "https://linkedin.com/in/alex",
    "confidence": 0.9,
}
ENRICH_SCHEMA = {
    "domain": "string",
    "role": "string",
    "email": "string",
    "evidence_url": "string",
    "confidence": "number",
}


def test_hire_submit_rejects_denied_tool(service, make_agent):
    from services.agent_platform.exceptions import SubmissionValidationError

    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    company = service.register_company(email="trace@acme.test")
    listing = _sla_listing(service, agent)
    hire = service.create_hire(company_id=company.id, listing_id=listing.id)
    job = service.create_job(company_id=company.id, listing_id=listing.id, row_count=1, hire_id=hire.id)
    service.notify_job_funded(
        job_id=job.id,
        agent_id=agent.id,
        category="sales_lead_generation",
        objective_schema=ENRICH_SCHEMA,
    )
    try:
        service.submit(
            job_id=job.id,
            agent_id=agent.id,
            payload=ENRICH_PAYLOAD,
            trace={"tools_used": ["browser.unrestricted"]},
        )
        raise AssertionError("expected SubmissionValidationError")
    except SubmissionValidationError:
        pass


def test_hire_submit_accepts_allowlisted_tools(service, make_agent):
    agent, _, _ = make_agent(categories=["sales_lead_generation"])
    company = service.register_company(email="oktrace@acme.test")
    listing = _sla_listing(service, agent)
    hire = service.create_hire(company_id=company.id, listing_id=listing.id)
    job = service.create_job(company_id=company.id, listing_id=listing.id, row_count=1, hire_id=hire.id)
    service.notify_job_funded(
        job_id=job.id,
        agent_id=agent.id,
        category="sales_lead_generation",
        objective_schema=ENRICH_SCHEMA,
    )
    submission = service.submit(
        job_id=job.id,
        agent_id=agent.id,
        payload=ENRICH_PAYLOAD,
        trace={"tools_used": ["http.fetch", "hunter.email"]},
    )
    assert submission.harness_ok is True
    assert submission.trace_digest

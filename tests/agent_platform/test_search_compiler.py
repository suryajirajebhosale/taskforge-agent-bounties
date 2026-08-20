from services.agent_platform.search_compiler import compile_search_query
from services.agent_platform.templates import EMAIL_VERIFY, LEAD_ENRICHMENT, RESUME_SCREEN


def test_vague_query_searches_all_specializations():
    compiled = compile_search_query("something vague")
    assert compiled.template_id is None
    assert compiled.sla_only is False


def test_hire_language_compiles_to_sla_filter():
    compiled = compile_search_query("hire a retainer agent")
    assert compiled.sla_only is True
    assert compiled.certified_or_better is True
    assert compiled.template_id is None


def test_budget_language_sets_credit_cap():
    compiled = compile_search_query("cheap ecommerce enrich")
    assert compiled.max_credits_per_row == 15
    assert compiled.template_id == LEAD_ENRICHMENT


def test_bounce_query_selects_email_verify():
    compiled = compile_search_query("verify bounce emails")
    assert compiled.template_id == EMAIL_VERIFY


def test_resume_query_selects_screen():
    compiled = compile_search_query("screen candidate resume")
    assert compiled.template_id == RESUME_SCREEN

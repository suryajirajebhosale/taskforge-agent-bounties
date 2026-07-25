# PRD: Bounty Requirement/Rubric Module

*Module 2 of 5 — Bounty marketplace build. Derived from [bounty-clone-plan.md](../../bounty-clone-plan.md), Phase 1/3.*

## Problem Statement

Requesters naturally describe what they want in free text ("find 100 ecommerce brands doing $1M–$25M in revenue"), but free text isn't machine-checkable. Without a structured definition of "done," agent developers have to guess at acceptance criteria, and the Oracle Verification Service has nothing concrete to grade a submission against — which undermines the platform's core promise of paying automatically only for verified results.

## Solution

A module that converts a requester's free-text bounty description into a structured, editable `Requirement` — a mix of objective, machine-checkable criteria and subjective, rubric-style criteria — using an LLM-assisted generation step, with mandatory requester review and approval before the bounty can be funded.

## User Stories

1. As a requester, I want to describe my bounty in plain English, so that I don't have to learn a rigid form or schema to post a task.
2. As a requester, I want the platform to propose structured acceptance criteria based on my description, so that I don't have to manually specify every checkable detail myself.
3. As a requester, I want to review and edit the generated criteria before funding my bounty, so that I retain control over exactly what "done" means for my money.
4. As a requester, I want to distinguish between objective requirements (e.g. "at least 100 leads") and subjective ones (e.g. "tone matches my brand"), so that I understand which parts of my bounty can be checked automatically versus judged.
5. As a requester, I want category-appropriate default criteria suggested (e.g. lead-gen bounties default to count/format/validity checks; content bounties default to tone/originality checks), so that the generated rubric is relevant to the kind of work I'm asking for.
6. As an agent developer, I want to see the exact structured requirements for a bounty before my agent attempts it, so that my agent knows precisely what will be checked.
7. As an agent developer, I want requirements to be locked once a bounty is funded, so that the goalposts can't move after my agent has started work.
8. As a platform engineer building the Oracle Verification Service, I want a well-formed, schema-validated `Requirement` object attached to every funded bounty, so that the grading pipeline always has a concrete target to check against.
9. As a platform engineer, I want objective criteria expressed as `(field, comparator, target value)` tuples, so that the Oracle's deterministic checker can evaluate them without any LLM involvement.
10. As a platform engineer, I want subjective criteria expressed as weighted rubric lines, so that the Oracle's LLM judge has a concrete, bounded rubric to grade against rather than an open-ended prompt.
11. As a platform operator, I want rubric generation quality tracked against a golden dataset of real bounty descriptions per category, so that regressions in generation quality are caught before they reach requesters.
12. As a platform operator, I want the rubric-generation model backend to be swappable (OpenAI or NVIDIA NIM), so that generation quality/cost tradeoffs can be tuned without rewriting this module.
13. As a requester who wants to reuse a bounty template, I want to see which category a generated rubric was based on, so that I can understand why certain default criteria were suggested.

## Implementation Decisions

- **Module:** `RubricGenerationService`, backed by a `RubricAgent` — an object-oriented LangChain agent class sharing a common base (`BaseLangChainAgent`) with the Oracle Verification Service's `JudgeAgent` and `DisputeAgent`, with a pluggable model backend (OpenAI default, NVIDIA NIM as a self-hostable alternative).
- **Data model (`Requirement`, Pydantic):**
  - `objective_criteria: list[ObjectiveCriterion]` — e.g. `field="lead_count", comparator=">=", value=100`.
  - `subjective_criteria: list[SubjectiveCriterion]` — free-text rubric line plus a weight, e.g. `"tone matches brand voice", weight=0.3`.
- **Interface:** `generate_rubric(bounty_description: str, category: BountyCategory) -> Requirement` produces a *draft*; the draft is shown to the requester in the posting UI for edit/approval. Only an **approved** `Requirement` can be attached to a funded `Bounty`.
- **Category templates:** each `BountyCategory` (Sales & Lead Generation, Research & Competitive Intelligence, AI Automation & Product Building, Hiring & Recruiting, Content & Media, Other) seeds generation with a default criteria shape, reducing LLM drift and improving objective-criteria extraction reliability.
- **Immutability:** a `Requirement` is locked once its `Bounty` is funded. Any change after funding must create a new bounty rather than mutate the existing one, so the Oracle always grades against a fixed, known target.

## Testing Decisions

Good tests check that generation produces **valid, schema-conformant** `Requirement` objects across a representative sample of real bounty descriptions per category — not that the LLM's output "sounds right" in a subjective sense.

- Golden-set regression tests: a fixed set of example bounty descriptions (spanning the observed categories) with expected structured criteria shapes, re-run whenever the `RubricAgent` prompt, category templates, or model backend changes.
- At minimum, every generated `Requirement` must pass Pydantic schema validation before being shown to the requester — downstream modules (the Oracle) depend on `Requirement` always being well-formed, so this validation is non-negotiable even though this module wasn't selected for the deepest test investment this round.
- Prior art: this module should reuse the same golden-dataset fixture format as the Oracle Verification Service's eval harness (see that PRD) so the two test suites stay consistent and comparable.

## Out of Scope

- Fully autonomous rubric approval with no requester review (a human always confirms before funding, for MVP).
- Multi-language bounty descriptions (English only for MVP).
- Editing a `Requirement` after a bounty has received submissions.

## Further Notes

This module is small in isolation but is the load-bearing interface between "what the requester actually asked for" and "what the Oracle can mechanically grade." Keep category templates dependency-injected/configuration-driven so new categories can be added without a code change.

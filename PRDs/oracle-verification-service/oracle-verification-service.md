# PRD: Oracle Verification Service

*Module 4 of 5 — Bounty marketplace build. Derived from [bounty-clone-plan.md](../../bounty-clone-plan.md), Phase 3.*

## Problem Statement

The platform's central promise — pay automatically, with no human reviewer, only when work is genuinely good — is worthless without a verification system trustworthy enough that requesters will fund real money against it and agent developers will accept a "fail" as fair. This is the single highest-risk technical component in the entire build: get it wrong, and neither side of the marketplace will trust the platform with real money.

## Solution

A standalone service that grades submissions against their bounty's `Requirement` (from the Bounty Requirement/Rubric Module) through a category-aware, multi-stage pipeline — deterministic checks, sandboxed execution, and LLM-judge grading — routes low-confidence or high-value verdicts to human review instead of auto-resolving, supports a dispute/appeal path, and is continuously regression-tested against a golden dataset so grading quality cannot silently drift over time.

## User Stories

1. As a requester, I want my bounty's submission automatically checked against the exact requirements I approved, so that I don't have to manually review every submission myself.
2. As a requester, I want a clear, human-readable explanation of why a submission passed or failed, so that I can trust the verdict instead of treating it as a black box.
3. As a requester, I want high-value bounties to get a human review before my escrow is released, so that I have extra confidence on the submissions that matter most financially.
4. As an agent developer, I want to know exactly why my agent's submission failed, so that I can improve my agent rather than guessing.
5. As an agent developer, I want to appeal a "fail" verdict I believe is wrong, so that a single bad grading run doesn't unfairly cost me the bounty and my reputation.
6. As an agent developer, I want an appeal to be graded independently (not just re-run the same way), so that I have genuine recourse, not a rubber stamp.
7. As an agent developer building a code-based agent, I want my submitted code actually executed and tested, not just described, so that grading reflects what my agent really built.
8. As an agent developer building a lead-generation agent, I want objective checks (counts, valid emails, no duplicates) applied deterministically, so that I'm not at the mercy of an LLM's subjective judgment for things that are actually checkable with certainty.
9. As a platform operator, I want every verdict to include a confidence score, so that low-confidence grading can be routed to a human instead of silently auto-resolving.
10. As a platform operator, I want a configurable per-category confidence threshold and bounty-value threshold for auto-resolution, so that I can tune how much automation vs. human review each category and price point gets.
11. As a platform operator, I want a queue of submissions routed to human review, so that reviewers have a clear worklist rather than needing to monitor the whole platform.
12. As a platform operator, I want the grading pipeline to be regression-tested against a golden dataset of real past submissions on every prompt, rubric-template, or model-version change, so that grading quality can't silently degrade without anyone noticing.
13. As a platform operator, I want false-positive and false-negative rates tracked over time using real dispute outcomes as ground truth, so that I have an actual accuracy metric for the oracle, not just a feeling.
14. As a platform operator, I want the LLM-judge model backend (OpenAI or NVIDIA NIM) to be swappable via configuration, so that I'm not locked into a single vendor as pricing or quality shifts.
15. As a platform operator, I want a disputed-and-overturned verdict to be logged and fed back into the golden dataset, so that the system learns from its own mistakes over time.
16. As a platform engineer, I want the deterministic-checks stage, sandboxed-execution stage, and LLM-judge stage to be independently callable and independently testable, so that a bug or regression in one stage doesn't require re-verifying the whole pipeline by hand.
17. As a platform engineer integrating the Escrow Ledger Service, I want a final `Verdict` to unambiguously trigger exactly one of `release_to_agent` or `refund_to_requester`, so that escrow and grading state can never disagree about what should happen next.
18. As a security-conscious platform engineer, I want sandboxed code execution to run with strict resource and time limits in full isolation, so that a malicious or buggy agent submission can't affect the platform's own infrastructure.

## Implementation Decisions

- **Module:** `OracleVerificationService` (FastAPI), owning:
  - `Verdict` — `submission_id`, per-stage results, `final_result` (pass/fail), `confidence: float`, `rationale: str`, `routed_to_human: bool`.
  - `DisputeCase` — `verdict_id`, `raised_by`, `resolution`, `resolved_by`.
- **Pipeline stages** (run in order, category-aware per `BountyCategory`):
  1. **`DeterministicChecker`** — validates the submission against `Requirement.objective_criteria` (schema/format/field/count checks); performs duplicate/near-duplicate detection via `pgvector` embeddings for Sales & Lead Generation / Research & Competitive Intelligence categories.
  2. **`SandboxExecutor`** — for AI Automation & Product Building submissions, runs the submitted code and its tests inside an isolated Docker or Firecracker microVM sandbox with strict resource/time limits; captures stdout and exit codes as structured evidence passed to the next stage.
  3. **`JudgeAgent`** — an object-oriented LangChain agent class (sharing a `BaseLangChainAgent` base with the Rubric Module's `RubricAgent` and this service's own `DisputeAgent`), with a pluggable model backend (OpenAI default, NVIDIA NIM alternative). Grades `Requirement.subjective_criteria` against the submission plus evidence from stages 1–2, and returns a structured `{verdict, confidence, rationale}` via tool-calling/structured output — never free-text-only output.
  4. **`ConfidenceRouter`** — combines all stage results into the final `Verdict`. If `confidence >= threshold` (configurable per category) **and** the bounty amount is below a configurable human-review threshold, auto-resolves — calling the Escrow Ledger Service's `release_to_agent` or `refund_to_requester` directly. Otherwise, creates a human review task.
- **Dispute flow:** an agent developer can appeal a "fail." The `DisputeAgent` (same base class as `JudgeAgent`, different prompt for judge diversity) re-grades independently; combined with an optional human escalation step. `DisputeCase.resolution` is final once set, and is logged as a labeled example fed back into the eval harness below.
- **Eval harness:** `services/oracle/evals/` holds a golden dataset of real (anonymized) past submissions per category with known-correct verdicts. A CI job runs the full pipeline against this golden set on every change to prompts, rubric templates, or model version; tracks false-positive/false-negative rate over time; **blocks deploy** if regression exceeds a defined threshold.
- **Model-backend consistency:** `JudgeAgent`, `RubricAgent` (Requirement module), and `DisputeAgent` all share `BaseLangChainAgent` with the model backend injected as configuration, so switching OpenAI ↔ NVIDIA NIM is a config change across the whole oracle, not a code change in three places.

## Testing Decisions

Good tests separate **deterministic-stage tests** (pure function-style: given a payload and criteria, assert pass/fail — no LLM involved, fast, fully reliable, exact-match assertions are appropriate) from **LLM-judge tests** (evaluated against the golden dataset with accuracy/calibration thresholds, since LLM output isn't perfectly deterministic — exact-match assertions are the wrong tool here).

- Cover: each deterministic checker in isolation (format, count, duplicate detection) with clear pass/fail fixtures; the sandbox executor correctly captures pass/fail from real code execution using known-good and known-bad sample repos; the confidence router correctly routes to auto-resolve vs. human queue at threshold boundaries (including edge cases exactly at the threshold); dispute re-grading is verifiably independent of the original grading run, not a repeat of the same call; the eval harness itself is tested to correctly compute false-positive/false-negative rates from a fixture set with known labels.
- This module was selected for dedicated test investment, alongside the Escrow Ledger Service — together these two modules are what make "pay automatically" safe to promise at all.
- Prior art: none yet in-repo. This PRD, together with the Rubric Module's golden-dataset approach, establishes the pattern for future LLM-graded modules in this codebase — the two should share fixture format so golden examples can potentially be reused across both.

## Out of Scope

- Fully automated dispute resolution with no human escalation path (a human escalation option is always available in MVP, even if rarely used).
- Cross-category transfer learning in the judge (each category's rubric and prompt are tuned independently for MVP, not a single universal judge across all categories).
- Real-time/streaming verification while an agent is still working (submissions are graded asynchronously after intake, not mid-execution).

## Further Notes

This is the module most likely to determine whether the platform is trusted at all — more so than the marketplace UI, which is comparatively easy to build. The eval harness and golden dataset should be built **in parallel with the pipeline itself**, not as a follow-up task after launch; treat the Testing Decisions above as part of the initial build scope, not a stretch goal.

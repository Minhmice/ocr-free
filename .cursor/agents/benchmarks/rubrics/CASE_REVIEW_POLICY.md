# Case Review Policy

## Scope

Applies to:

- `cases/*.jsonl` (including adversarial + mutation cases)
- `expected/expected_results.json`
- `expected/golden_summary.json`
- `scripts/predictor.py`
- `scripts/run_benchmark.py`, `scripts/score_benchmark.py`, `scripts/validate_cases.py`

Goal: keep benchmark deterministic, auditable, and resistant to overfitting.

## When expected outputs may be changed

Expected outputs **may change** only when at least one is true:

- **Objectively wrong**: current expected contradicts repository ground truth (routing rules, contract, validator behavior).
- **Schema correction**: case violates required schema and cannot be evaluated deterministically without change.
- **Bug fix in harness**: scorer/runner bug made prior “expected vs actual” comparison incorrect; expectation must reflect intended behavior.

Expected outputs **must not change** to “make score go up” without evidence.

Required evidence in PR/commit message or report:

- what was wrong (quote failing diff from `summary_scored.json`)
- why new expected is correct (cite repo files / validator output substring)
- impact: updated score + failures

## When predictor may be changed

Predictor (`scripts/predictor.py`) changes allowed only when:

- fix false positive/negative in deterministic routing/classification/validation prediction
- align with updated routing rules/protocol docs
- reduce ambiguity (e.g., negation handling) without adding nondeterminism

Predictor changes must include:

- new/updated tests are out of scope (stdlib-only, no framework), so instead include:
  - a short “before/after” snippet in a phase report, and
  - updated adversarial coverage if needed

## Do not change predictor and expected in same change (default rule)

Default: **do not change** predictor and expected cases in same change.

Exception: allowed only if report explains why both must move together, and includes:

- old behavior and why wrong
- new predictor behavior and why correct
- expected updates strictly limited to cases objectively impacted
- golden comparison discussion

## Adversarial case acceptance criteria

Adversarial cases (`cases/adversarial.jsonl`) must:

- be **deterministic** under current predictor
- probe “near-collisions” (e.g., `research` vs `search`, negations like “do not change”)
- include **clear notes** stating why expected output is correct
- avoid relying on subjective phrasing (“sounds like…”) or LLM judgment

Adversarial cases must not:

- encode internal implementation details of predictor beyond observable outputs
- hardcode brittle strings that are unrelated to protocol

## Mutation case acceptance criteria (Layer D)

Layer D cases must:

- mutate **temp copy only** (runner responsibility)
- specify `mutation.type` in supported set
- include validation command(s) in expected (deterministic intent)
- optionally specify:
  - `expected_exit_code`
  - `expected_error_substrings` (stable, minimal substrings)

Layer D cases must not:

- reference absolute paths
- require network access
- depend on OS-specific error messages beyond stable substrings

## Golden baseline update procedure

`expected/golden_summary.json` is governance, not truth.

Update golden only when:

- intentional, reviewed change lands (predictor/harness/expected) and
- new baseline is accepted as “best known” behavior

Procedure:

- run:
  - `python .cursor/agents/benchmarks/scripts/validate_cases.py`
  - `python .cursor/agents/benchmarks/scripts/run_benchmark.py`
  - `python .cursor/agents/benchmarks/scripts/score_benchmark.py --actual .../actual_results.jsonl --golden .../golden_summary.json`
- if change is intended:
  - update `golden_summary.json` to new baseline score/failure counts
  - record entry in `reports/HISTORY.md`

## Anti-overfitting rules

- Prefer **new adversarial cases** over tweaking old expected outputs.
- Do not add keyword hacks that only satisfy one case; require at least:
  - one baseline case, and
  - one adversarial case
  to benefit from a predictor change.
- Keep negation handling conservative: avoid “change verb” being triggered by “do not change …”.
- Keep short keyword matching token-aware (avoid substring traps like `ui` in `suite`).


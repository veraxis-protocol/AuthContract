# Repository usability test (AC-036)

A clean-room test of the repository as a **product surface**: can an unfamiliar
developer, following only `README.md`, understand what this is and get a
meaningful result quickly?

Performed against commit `35e2bef2060d113cefaf13f8c1da2a08c47559ac` from a
genuinely fresh `git clone` — no reused virtualenv, no undocumented local
state, no commands invented outside the README.

This document records observations. **It does not self-certify Gate E**; that
adjudication belongs to the Engineering Lead.

---

## Environment

| | |
|---|---|
| OS | Linux 6.18.44 x86_64 |
| Python | 3.11.15 (README requires ≥3.10) |
| git | 2.43.0 |
| Network | clone + PyPI dependency install only |
| Credentials | none required, none supplied |

---

## Results

### A. ~30-second comprehension — PASS

The first screen (11 lines before the first `---`) delivers, in order: a
one-sentence definition, the `source → rule → PR → check → merge → runtime →
proof` chain, and an implementation-status note stating TRL 4, the
one-synthetic-specimen scope, and — unambiguously — that automated
natural-language source-to-rule comparison **is not implemented end to end**.

A reader who stops after 30 seconds leaves with a correct impression rather
than an inflated one. That was the specific failure mode before this change:
the prior README opened with ~400 lines of worked examples of the *target*
capability, so the most prominent material described behavior that does not
exist yet.

### B. Install + first meaningful success ≤ 5 minutes — PASS (~35 s)

| Step | Elapsed | Cumulative |
|---|---:|---:|
| `git clone` + `git checkout` | 1 s | 1 s |
| `python3 -m venv` + `pip install -e ".[test]"` | 11 s | 12 s |
| `pytest -q` → **342 passed** | 11 s | 23 s |
| `authcontract run-specimen …` → PASS/ALLOW + receipt | <1 s | **~24 s** |

Roughly **24 seconds** to a first meaningful end-to-end success, against a
five-minute budget. Even allowing for a cold PyPI cache and slower hardware,
the margin is large.

No undocumented state was required. Every command came from the README.

### C. Deliberate refusal reproducible — PASS (both cases)

**Refusal 1 — undeclared action.** Exit code `1`:

```json
{"status": "REFUSED", "reason_code": "RUN_UNCLASSIFIED_ACTION",
 "message": "RUN_UNCLASSIFIED_ACTION: 'issue_refund' is not in the closed mediated-action universe for this projection"}
```

**Refusal 2 — stale runtime fact.** Exit code `1`:

```json
{"status": "REFUSED", "reason_code": "RUN_FACT_STALE",
 "message": "RUN_FACT_STALE: secondary_approval.present is older than 0:15:00"}
```

Both match the README byte-for-byte in `status`, `reason_code`, and `message`.
Both correctly issue **no receipt** — a refused decision does not emit evidence
claiming a decision was made.

### D. Receipt verification reproducible — PASS

```json
{"status": "PASS", "reason_code": "OK", "receipt": "receipt_valid.json", …}
```

Exit code `0`, matching the README. Verification recomputes every bound value
from the raw artifact, action, and fact files and trusts no field in the
receipt itself.

### E. Integration path findable and understandable — PASS

`## How to integrate it today` names four available interfaces (CLI, Python
library, GitHub merge gate, runtime invocation/receipt verification) and one
explicit **Not available** list.

The Python example was executed verbatim from the README in the clean clone:

```
ALLOW OK
PASS OK
```

The "Not available" list is as load-bearing as the available one — it states
plainly that there is no published package, no HTTP/gRPC service, no
persistence layer, no multi-contract registry, and no replay protection.

---

## Findings

**U1 — Licensing is declared.** The root `LICENSE` contains the PolyForm
Noncommercial License 1.0.0 and `pyproject.toml` identifies that file.
Commercial use requires a separate written license from Veraxis. This does not
make the project open source or establish third-party license compatibility.

**U2 — The README is long (1,215 lines).** The runnable product surface is the
first ~250; the remainder is conceptual material describing target behavior,
now explicitly fenced under "How it works — the full model". A future pass
could move that body into `docs/`, but doing so here would have exceeded
AC-036's product-surface scope and risked disturbing accepted
developer-language content.

**U3 — Documentation guards constrain README structure, correctly.** The
AC-021/AC-021A/AC-021B tests pin specific README sentences and one structural
invariant (deep ontology vocabulary must sit below `## Quick start`). The first
draft of this restructure broke three of them; all were restored, none was
weakened. Anyone editing the README should expect these guards to fire — they
are a feature, and they caught genuine claim-ceiling drift here.

**U5 — The benchmark's DUT guard treats `README.md` as a protected surface, so
documentation-only changes trip it.** Running `benchmarks/run_benchmarks.py` on
this branch exits `2` with `DUT DRIFT: 1 file(s) differ` — that file being
`README.md`. This is the guard behaving **correctly**: it refuses to publish
results claiming to describe `e4e1a975` when any declared device-under-test
path differs, and `README.md` is in that list because AC-035A protected it.

It was deliberately **not** worked around. Weakening the guard, or trimming
`README.md` out of `DUT_PATHS`, to make a documentation PR go green would
defeat the property the guard exists to provide.

No behavioral regression is possible from this change: `authcontract/`,
`tests/`, `fixtures/`, `.github/`, `pyproject.toml`, and `benchmarks/` are
**byte-identical** to merged main `4c90aa79dd922888a8beb3aa9d886c44ecc28c7c`,
where the full benchmark last ran 7/7 end-to-end and 38/38 adversarial with
exit `0`. The only file changed against that commit is `README.md`.

A future refinement could split `DUT_PATHS` into behavioral and documentary
sets, so doc changes are reported without blocking. That is a benchmark-design
decision, out of scope for AC-036.

**U4 — CLI output is single-line JSON.** Readable via `jq` or `python3 -m
json.tool`, but not pretty-printed natively. The README reflows it for
readability and says so explicitly, rather than implying prettier output than
the CLI produces.

---

## Not tested

- Windows and macOS. Linux only.
- Python 3.10 and 3.12 were not exercised here, though repository CI covers both.
- Cold-cache install timing on constrained networks.
- Comprehension by an actual unfamiliar human. This test was performed by the
  same party that wrote the README, which is a real limitation: it can
  establish that the documented path *works*, but not that the explanation
  *lands* for a genuine newcomer. Independent review remains the gap.

# Validation record

## Completed

- Local Python 3.12: **29 passing tests** at the final backend verification pass.
- Typed request rejection, persistence roundtrip, conflicting idempotency keys, concurrent SQLite writes, token enforcement, and the request-size boundary.
- All three included scenarios reproduce their expected outcomes in evidence-engine mode.
- Mock HTTP transport exercises the Ollama request schema, JSON response parsing, HTTP failure, malformed response, and response-size budget.
- Domain tests exercise lineage scoping, healthy controls, abstention, and rejection of invented or misassigned AI evidence IDs.

- Browser smoke checks: real API-backed scenario runs, evidence/replay tab, editable request view, saved-run reload, JSON import/export, and mobile layout; no browser JavaScript errors observed.

## What these results do not establish

- No actual local model was available in the authoring environment. Model inference quality, model latency, and hardware suitability are unmeasured.
- Docker was unavailable; the Dockerfile and Compose configuration were not executed.
- GitHub Actions includes Python 3.11/3.12/3.13. Local testing covered Python 3.12; see the repository Actions page for remote execution status after publication.
- Synthetic fixtures are deliberately small. They are regression scenarios, not an unbiased quality benchmark.
- No enterprise source systems or user credentials were used. Live integrations need separate validation.
- The current HTTP test stack emits an upstream Starlette/httpx deprecation warning; tests pass. A future dependency refresh should migrate the test transport when supported.

## Reproduction

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python scripts/evaluate.py
```

Both documented CLI commands were executed successfully. Local README/LLD links resolve, and the editable architecture XML parses with anchored connectors.

The browser workbench is a real client of the API. The screenshot in README is captured from the running app against synthetic data.

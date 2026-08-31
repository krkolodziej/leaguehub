# Optional AI match reports

When a match enters `FINISHED`, a post-commit Celery task builds a minimal
structured summary (teams, score, and goal events) and asks a
`MatchReportGenerator` provider for a short report. The report is stored in the
separate `MatchReport` model and exposed at the match `report/` endpoint.

The default `template` provider is deterministic and offline. Set
`AI_MATCH_REPORT_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally
`OPENAI_MODEL` to use the OpenAI Responses API with strict JSON output. The raw
response is treated as untrusted data and validated for shape and length before
it is persisted. Provider failures mark only the report as `FAILED`; match
state, scores, standings, and notifications are unaffected.

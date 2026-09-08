# Northstar Companion

*Engineering Reliable AI Agents* · Murad Malachiev · First edition, 2026

Original fictional teaching project for *Engineering Reliable AI Agents*. Python 3.11+; standard library only. The local identities are fixtures, not an authentication service.

```bash
python3 test_northstar.py
python3 test_mcp.py
python3 make_scenarios.py
python3 summarize_trials.py --check
python3 northstar.py demo --db /tmp/northstar-demo.db
```

The demo stops at `needs_approval` and leaves the ticket OPEN. Use a fresh database path for a clean scenario. Appendix A contains the separate exact-proposal review and commit walkthrough. The fixture's current-policy query assumes a reading date on or after 2026-08-01. No migration from earlier development schemas is provided; use a fresh demonstration database.

`offline-check-report.json` records 29 passing component checks. The separate MCP and trial-summary checks exercise transport and arithmetic. These are not live-model evaluations or production security certification. The Chapter 15 code sample is a separate small boundary-predicate exercise, not another hidden Northstar subsystem.

## Optional live model

Set `ANTHROPIC_API_KEY` using your normal local secret management, then choose an available model ID:

```bash
python3 northstar.py live --model YOUR_AVAILABLE_MODEL --db /tmp/northstar-live.db
```

This makes billable Anthropic Messages requests. The companion includes no live-model benchmark results. Record actual model, date, prompts, fixture, usage and limits. Local byte admission is an estimate; a hard currency budget needs an external price-aware reservation mechanism. Provider errors are returned without an automatic retry loop.

## Scope and limits

- `northstar.py`: tenant-scoped reads, explicit dispatch, scripted or optional live model, durable observations, exact proposals, scoped approval, local transactional commit, material-evidence freshness and idempotent replay. Receipt replay is restricted to the original actor with current local read/approve/commit scopes.
- `mcp_read_server.py`: real MCP 2025-11-25 stdio exchange; exactly four local read tools, fixed Cedar principal. No HTTP listener or remote authentication.
- `scenarios.jsonl`: 200 original specifications in 40 families; 120 development, 80 held out. Five variants share each family. Additional fixture provisioning and expert review are required before a live benchmark.
- `summarize_trials.py`: summarize supplied explicitly graded trials; does not grade prose, provision scenarios, or claim missing trials occurred. Costs must include the cost components your declared study counts and use one unit. Example schema is in its module help.
- The browser supervision panel is a local interaction prototype and has no database connection. HTTP service design, distributed cancellation, leases, A2A deployment, vector/graph comparisons and human studies are documented extensions, not implemented production capabilities.

Use source-controlled snapshots and hashes for a live comparison. Record task family and trial identities separately. Keep failed attempts and human work in totals. Never interpret the deterministic scripted model as evidence of LLM competence.

## Files and version

First-edition companion, September 2026. No third-party Python dependencies. MCP reference revision: 2025-11-25. Live provider model is reader-selected; see the primary references in the book before execution.

See `CHAPTER-CHECKPOINTS.md` for the progression through the runnable surfaces and reference designs. See `ERRATA.md` for the correction workflow. All Northstar policies and data are fictional and original; the source books are not redistributed.

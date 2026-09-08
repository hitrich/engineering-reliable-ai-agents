# Chapter checkpoints

One main implementation keeps the action contract consistent. These checkpoints identify the runnable surface for each stage; they are not claims that separate production releases or live benchmarks exist.

| Stage | Chapters | Runnable checkpoint | Expected result |
| --- | --- | --- | --- |
| Baseline | 1–3 | `Store.seed()` then `baseline(store, INVESTIGATOR)` | Supported current-limit comparison with zero model calls |
| Bounded loop | 3 | `python3 northstar.py demo --db /tmp/ns-loop.db` | Four reads and a proposal; `needs_approval`; ticket remains OPEN |
| Controlled action | 4 | Appendix A's exact-proposal walkthrough on a fresh database | Reviewer approves exact content; transaction verifies one update |
| Evidence and state | 5–6 | Inspect policy records and the persisted `runs` table; restart check in `test_northstar.py` | Current policy selection and durable authorized observations |
| Recovery and boundaries | 7–9 | `python3 test_northstar.py` | 29 local checks; the report explicitly distinguishes them from model evaluation |
| Supervision | 10 | `../agent-explorer.html?view=review` | Keyboard-accessible local preview states; no database connection |
| Coordination | 11 | Chapter 11 and Appendix B experiment 5 | Concrete comparison protocol; no fabricated multi-agent result |
| Interoperability | 12 | `python3 test_mcp.py` | Real stdio discovery/read exchange and rejection cases |
| Operation and performance | 13–14 | Reference service/rollback contracts; `python3 summarize_trials.py --check` | Checked arithmetic and explicit deployment/benchmark limits |
| Domain transfer | 15 | Standalone `exceeds_limit` exercise in the chapter | Boundary checks distinguish an inclusive limit from excess |
| Release | 16 | Review README, ERRATA, scenario manifest and Chapter 16 | Named ownership roles, pilot gates and required evaluation evidence |

For a repeatable run, use a new database path or the temporary databases created by the checks. Do not reset a user's actual records. The included scenario data are fictional specifications; provisioning all 200 environments is separate work described in Appendix B.

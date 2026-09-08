"""Run: python3 test_northstar.py. Offline component tests, not an LLM evaluation."""
import json
import tempfile
import time
from pathlib import Path
from northstar import (Store, Principal, INVESTIGATOR, REVIEWER, BoundaryError,
                       dispatch, baseline, run_agent, ScriptedModel)


def check_rejected(operation, expected):
    try:
        operation()
    except BoundaryError as error:
        assert expected in str(error), (expected, str(error))
    else:
        raise AssertionError("Expected rejection: " + expected)


def fresh():
    store = Store()
    store.seed()
    return store


def propose(store, suffix=""):
    return store.propose(INVESTIGATOR, "T-104", 1,
                         "18,432 rows exceeds the current 10,000-row Standard limit. " + suffix)


def main():
    passed = []
    def check(name, operation):
        operation()
        passed.append(name)

    store = fresh()
    check("authorized ticket read", lambda: assert_equal(store.read(INVESTIGATOR, "read_ticket", "T-104")["tenant"], "Cedar"))
    check("tenant selected from trusted principal", lambda: assert_equal(store.read(Principal("Juniper", "u", frozenset({"read"})), "read_ticket", "T-104")["tenant"], "Juniper"))
    check("missing scope denied", lambda: check_rejected(lambda: store.read(Principal("Cedar", "u", frozenset()), "read_ticket", "T-104"), "permission_denied"))
    check("unknown tool denied", lambda: check_rejected(lambda: dispatch(store, INVESTIGATOR, "send_email", {}), "unknown_tool"))
    check("extra tenant argument denied", lambda: check_rejected(lambda: dispatch(store, INVESTIGATOR, "read_ticket", {"ticket_id": "T-104", "tenant": "Juniper"}), "invalid_fields"))
    check("boolean version denied", lambda: check_rejected(lambda: dispatch(store, INVESTIGATOR, "propose_update", {"ticket_id": "T-104", "expected_version": True, "draft_reply": "x" * 30}), "invalid_integer"))
    check("oversized draft denied", lambda: check_rejected(lambda: propose(store, "x" * 2100), "invalid_draft"))
    check("SQL-shaped identifier is not executed", lambda: check_rejected(lambda: dispatch(store, INVESTIGATOR, "read_ticket", {"ticket_id": "' OR 1=1 --"}), "not_found"))
    check("current policy excludes superseded limit", lambda: assert_equal(store.read(INVESTIGATOR, "read_policy", "Standard")["limit_rows"], 10000))
    check("baseline solves known fixture without model", lambda: assert_equal(baseline(store, INVESTIGATOR)["state"], "supported"))
    proposal = propose(store)
    check("proposal leaves business record unchanged", lambda: assert_equal(store.read(INVESTIGATOR, "read_ticket", "T-104")["status"], "OPEN"))
    check("commit requires approval", lambda: check_rejected(lambda: store.commit(REVIEWER, proposal["proposal_id"], "test-key-001"), "approval_missing"))
    check("worker cannot approve", lambda: check_rejected(lambda: store.approve(INVESTIGATOR, proposal["proposal_id"], proposal["digest"]), "permission_denied"))
    check("approval binds displayed digest", lambda: check_rejected(lambda: store.approve(REVIEWER, proposal["proposal_id"], "wrong"), "changed_proposal"))
    check("cross-tenant proposal inaccessible", lambda: check_rejected(lambda: store.proposal(Principal("Juniper", "u", REVIEWER.scopes), proposal["proposal_id"]), "not_found"))
    alternate = propose(store, "Alternative wording.")
    store.approve(REVIEWER, proposal["proposal_id"], proposal["digest"])
    first = store.commit(REVIEWER, proposal["proposal_id"], "test-key-001")
    check("authorized update verifies status and version", lambda: assert_equal((first["status"], first["version"]), ("INVESTIGATED", 2)))
    check("lost response replay returns one committed effect", lambda: assert_equal(store.commit(REVIEWER, proposal["proposal_id"], "test-key-001"), first))
    check("replayed receipt still requires read scope", lambda: check_rejected(lambda: store.commit(Principal("Cedar", "reviewer-1", frozenset({"approve", "commit"})), proposal["proposal_id"], "test-key-001"), "permission_denied"))
    check("receipt remains bound to original actor", lambda: check_rejected(lambda: store.commit(Principal("Cedar", "reviewer-2", REVIEWER.scopes), proposal["proposal_id"], "test-key-001"), "receipt_actor_mismatch"))
    check("idempotency key cannot bind different proposal", lambda: check_rejected(lambda: store.commit(REVIEWER, alternate["proposal_id"], "test-key-001"), "idempotency_conflict"))
    store = fresh(); proposal = propose(store)
    store.approve(REVIEWER, proposal["proposal_id"], proposal["digest"])
    store.db.execute("UPDATE tickets SET version=2 WHERE tenant='Cedar'")
    check("stale approval rejected at commit", lambda: check_rejected(lambda: store.commit(REVIEWER, proposal["proposal_id"], "stale-key-01"), "stale"))
    store = fresh(); proposal = propose(store)
    store.approve(REVIEWER, proposal["proposal_id"], proposal["digest"])
    store.db.execute("UPDATE proposals SET expires=?", (time.time() - 1,))
    check("expired approval rejected", lambda: check_rejected(lambda: store.commit(REVIEWER, proposal["proposal_id"], "expired-key-01"), "expired"))
    store = fresh(); proposal = propose(store)
    store.approve(REVIEWER, proposal["proposal_id"], proposal["digest"])
    store.db.execute("UPDATE proposals SET changes=?", ('{"status":"CLOSED","draft_reply":"altered"}',))
    check("tampered proposal rejected", lambda: check_rejected(lambda: store.commit(REVIEWER, proposal["proposal_id"], "tamper-key-01"), "integrity"))
    store = fresh(); proposal = propose(store)
    store.approve(REVIEWER, proposal["proposal_id"], proposal["digest"])
    store.db.execute("UPDATE accounts SET plan='Pro' WHERE tenant='Cedar'")
    check("changed account evidence invalidates approval", lambda: check_rejected(lambda: store.commit(REVIEWER, proposal["proposal_id"], "evidence-key-01"), "material_evidence_changed"))
    store = fresh(); proposal = propose(store)
    store.db.execute("UPDATE proposals SET expires=?", (time.time() - 1,))
    renewed = propose(store)
    check("expired proposal requires a new approval identity", lambda: assert_equal(renewed["proposal_id"] != proposal["proposal_id"], True))
    empty = run_agent(store, INVESTIGATOR, lambda messages, timeout: {"content": [], "usage": {}})
    check("empty model response is not an answer", lambda: assert_equal((empty["state"], empty["error"]), ("failed", "empty_model_answer")))
    with tempfile.TemporaryDirectory() as folder:
        path = str(Path(folder) / "state.db")
        store = Store(path); store.seed()
        paused = run_agent(store, INVESTIGATOR, ScriptedModel(), max_steps=2)
        check("step cap stops the run", lambda: assert_equal(paused["state"], "stopped"))
        store.db.close(); store = Store(path)
        resumed = run_agent(store, INVESTIGATOR, ScriptedModel(), run_id=paused["run_id"])
        check("restart resumes durable observations", lambda: assert_equal((resumed["state"], resumed["steps"]), ("needs_approval", 5)))
        check("agent run cannot commit", lambda: assert_equal(store.read(INVESTIGATOR, "read_ticket", "T-104")["status"], "OPEN"))
    report = {"kind": "offline_component_checks", "checks_passed": len(passed),
              "checks": passed, "live_model_trials": 0, "human_studies": 0,
              "limitation": "Deterministic fixtures test the implementation's stated boundaries; they do not measure model quality or establish production security."}
    Path(__file__).with_name("offline-check-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def assert_equal(actual, expected):
    assert actual == expected, (actual, expected)


if __name__ == "__main__":
    main()

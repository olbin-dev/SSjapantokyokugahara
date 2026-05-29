# Milestone 1: Causa Core

This document defines the first safe implementation boundary for the Anchor DB ("Causa") project.

## SQLite Schema Design

```sql
CREATE TABLE AnchorCase (
    id TEXT PRIMARY KEY,
    user_intent TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE UISnapshot (
    id TEXT PRIMARY KEY,
    anchor_case_id TEXT NOT NULL,
    ax_tree_json TEXT NOT NULL,
    image_hash TEXT NOT NULL,
    FOREIGN KEY(anchor_case_id) REFERENCES AnchorCase(id)
);

CREATE TABLE LLMProposal (
    id TEXT PRIMARY KEY,
    anchor_case_id TEXT NOT NULL,
    action_sequence TEXT NOT NULL,
    risk_level INTEGER NOT NULL,
    FOREIGN KEY(anchor_case_id) REFERENCES AnchorCase(id)
);

CREATE TABLE HumanApproval (
    id TEXT PRIMARY KEY,
    llm_proposal_id TEXT NOT NULL,
    approved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(llm_proposal_id) REFERENCES LLMProposal(id)
);

CREATE TABLE ExecutionEvent (
    id TEXT PRIMARY KEY,
    human_approval_id TEXT NOT NULL,
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(human_approval_id) REFERENCES HumanApproval(id)
);

CREATE TABLE OutcomeEvidence (
    id TEXT PRIMARY KEY,
    execution_event_id TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    post_execution_state TEXT,
    FOREIGN KEY(execution_event_id) REFERENCES ExecutionEvent(id)
);

CREATE TABLE ReplayPolicy (
    id TEXT PRIMARY KEY,
    anchor_case_id TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY(anchor_case_id) REFERENCES AnchorCase(id)
);
```

## Python Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AnchorCase:
    id: str
    user_intent: str
    created_at: datetime

@dataclass
class UISnapshot:
    id: str
    anchor_case_id: str
    ax_tree_json: str
    image_hash: str

@dataclass
class LLMProposal:
    id: str
    anchor_case_id: str
    action_sequence: str
    risk_level: int

@dataclass
class HumanApproval:
    id: str
    llm_proposal_id: str
    approved_at: datetime

@dataclass
class ExecutionEvent:
    id: str
    human_approval_id: str
    executed_at: datetime

@dataclass
class OutcomeEvidence:
    id: str
    execution_event_id: str
    success: bool
    post_execution_state: Optional[str]

@dataclass
class ReplayPolicy:
    id: str
    anchor_case_id: str
    expires_at: datetime
```

## Deterministic Replay Decision Function

```python
@dataclass
class ReplayDecision:
    status: str
    reason_code: str
    message: str
    anchor_case_id: Optional[str]

def determine_replay_decision(
    current_ui_snapshot: UISnapshot,
    historical_cases: list[dict],
    current_risk_level: int
) -> ReplayDecision:
    """
    Returns a ReplayDecision object containing the status, reason code, message, and anchor_case_id.
    """
    # Pseudo-implementation for documentation purposes
    pass
```

## Replay Eligibility Rule

A historical case may return `replay_candidate` only if:
- current UI snapshot exactly matches the historical UI fingerprint
- business object identity is verified
- action payload hash matches
- prior HumanApproval exists
- prior OutcomeEvidence exists and indicates success
- ReplayPolicy is valid and not expired
- current risk level is below Risk 3
- no safety constraint is violated

Otherwise:
- Risk 3 or higher => `requires_human_anchor`
- failed prior outcome => `do_not_replay`
- partial UI match => `requires_llm_reasoning`
- expired ReplayPolicy => `requires_human_anchor`

## Unit Test Cases

- **exact UI match + Risk 1 + successful outcome:** Should return `replay_candidate`.
- **exact UI match + Risk 3:** Should return `requires_human_anchor`.
- **failed prior outcome:** Should return `do_not_replay`.
- **partial UI match:** Should return `requires_llm_reasoning`.
- **expired replay policy:** Should return `requires_human_anchor`.

## Schema Notes

The initial schema is conceptual. The implementation version should consider adding:
- ui_fingerprint_hash
- business_object_id
- action_payload_hash
- app_bundle_id
- app_version
- outcome_status
- replay_allowed
- risk_threshold
- required_match_score

## Storage Abstraction

- Causa Core is storage-agnostic
- decision.py must remain independent from storage
- the in-memory repository is only for tests and local simulation
- SQLite is the initial local persistence target
- PostgreSQL / Supabase can be added later via storage adapters
- replay decisions must not depend on a specific database backend

## AnchorRecord Aggregation

- AnchorRecord represents one logical precedent case
- It groups AnchorCase, UISnapshot, LLMProposal, HumanApproval, ExecutionEvent, OutcomeEvidence, and ReplayPolicy
- It may be partial because missing evidence must remain representable
- Replay decisions still require explicit validation by decision.py
- AnchorRecord is a convenience aggregation, not an automatic replay permission

## AnchorRecord Decision Adapter

- The adapter allows replay decisions to be made from a full AnchorRecord
- It accepts AnchorRecord or None because repositories may not find a matching record
- It is only a convenience wrapper around determine_replay_decision
- It does not perform persistence
- It does not query repositories
- It does not grant replay permission by itself
- ReplayDecision remains the authoritative output

## Audit Summary

- ReplayDecision is the authoritative machine-readable result
- AuditSummary is the human-readable explanation layer
- AuditSummary does not grant replay permission
- AuditSummary does not perform execution
- AuditSummary does not query storage
- AuditSummary exists to make decisions reviewable and auditable

## Non-executing End-to-End Simulation

- Causa Core can now simulate the full decision path without executing any action
- The simulated path is:
  AnchorRecord -> Repository -> ReplayDecision -> AuditSummary
- These tests prove integration of the core layers
- They do not perform OS operations
- They do not perform autonomous replay
- They do not use external storage

## Milestone Completion

Milestone 1 is considered complete for v1.0-alpha as:
- AnchorRecord exists
- ReplayDecision exists
- AuditSummary exists
- InMemoryRepository exists
- non-executing E2E tests pass

## Safety Constraints

- No OS execution yet
- No sudo or privilege escalation logic
- No destructive operations
- No Dify integration yet
- No Accessibility API calls yet
- No autonomous replay yet
- LLM proposals must never self-approve risky actions
- HumanApproval and OutcomeEvidence must be stored separately
- A previous HumanApproval proves only that the user approved an action; it does not prove that the action succeeded
- Replay eligibility requires both a valid HumanApproval record and a successful OutcomeEvidence record

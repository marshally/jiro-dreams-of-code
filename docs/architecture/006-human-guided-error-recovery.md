# ADR-006: Human-Guided Error Recovery

## Status

Accepted

## Context

When jiro encounters failures during execution—validation errors, merge conflicts, stuck agents—it needs a recovery strategy. Options range from fully automatic retry to complete human takeover.

Key considerations:

- Automatic retry may repeat the same mistake
- Silent skipping hides problems
- Full human takeover is disruptive
- Agent may lack context to understand what went wrong

## Decision

Implement human-guided error recovery: on any failure, HALT immediately and require human input to continue.

### On Halt

1. **Terminal output**: Clear error message explaining what failed
1. **Exit code**: 5 (operation halted)
1. **Database record**: "Halted" status with reason stored in sessions table
1. **Interactive mode**: Option to transition directly to chat session

### Recovery Flow

```
HALT detected
    │
    ▼
Human reviews logs and halt reason
    │
    ▼
Human diagnoses issue (may involve manual fixes)
    │
    ▼
Human provides resume prompt with guidance
    │
    ▼
jiro execute --resume "Fixed X, continue with Y"
```

The resume prompt gives the agent context about:

- What was fixed
- How to proceed
- Any changed assumptions

### No Automatic Retry

Jiro does **not**:

- Retry failed operations automatically
- Skip failed tasks and continue
- Guess what went wrong
- Make assumptions about fixes

## Consequences

### Positive

- **No silent failures**: Every problem surfaces to human
- **Human judgment**: Human decides how to fix and whether to continue
- **Context preservation**: Resume prompt transfers human's understanding to agent
- **Audit trail**: Halt records show what failed and why
- **Safety**: Agent doesn't compound errors with bad guesses

### Negative

- **Blocks on human**: Can't make progress while waiting for human
- **Disruptive**: Human must context-switch to investigate
- **Overhead**: Simple issues that could self-heal require human intervention

### Mitigations

- Clear error messages help human diagnose quickly
- Interactive chat mode lets human and agent collaborate on fix
- Logs capture full context for diagnosis
- Future: notification channels (Slack, email) alert human remotely

## Alternatives Considered

1. **Automatic retry with backoff**: May work for transient errors but repeats logical errors
1. **Skip and continue**: Hides problems; downstream tasks may depend on skipped work
1. **Agent self-diagnosis**: Expensive (Opus cost) and may misdiagnose
1. **Checkpoint and rollback**: Complex to implement; still needs human to decide next step
1. **Tiered recovery**: Auto-retry for some errors, halt for others; complex to categorize correctly

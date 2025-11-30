# ADR-003: Model Selection Strategy (Brain/Hands Split)

## Status

Accepted

## Context

Jiro uses multiple AI agents for different tasks: spec generation (dreaming), task planning, task execution, and commit review. Each agent type has different requirements:

- **Dreaming/Planning**: Requires deep understanding, complex reasoning, and creativity
- **Execution**: Follows detailed plans mechanically, performing many granular steps
- **Review**: Validates commits against rules, needs good judgment but less creativity

We need to balance capability against cost, especially for execution where there may be dozens of granular tasks per session.

## Decision

Use a "brain/hands" split architecture:

| Agent | Model | Role |
|-------|-------|------|
| Dreaming | Opus 4.5 (latest) | The "brain" - generates specs from prompts |
| Planning | Opus 4.5 (latest) | The "brain" - produces detailed execution plans |
| Execution | Haiku (latest) | The "hands" - mechanically follows plans |
| Review | Sonnet (latest) | Validates commits, good judgment at lower cost |

**Key principle**: Planning uses Opus to do the smart work once, producing detailed step-by-step plans. Execution uses Haiku to follow those plans mechanically many times.

Always use the latest available version of each model family.

## Consequences

### Positive

- **Cost optimization**: Haiku is significantly cheaper than Opus; since execution has many steps, this adds up
- **Reliability**: Execution agent follows plans exactly, reducing variance
- **Quality where it matters**: Opus handles the complex reasoning in planning
- **Clear separation**: Planning decides what to do; execution does it

### Negative

- **Execution limitations**: Haiku may struggle if plans are ambiguous or incomplete
- **Planning dependency**: Quality of execution depends entirely on plan quality
- **No execution autonomy**: Agent can't adapt if it discovers something unexpected

### Mitigations

- Planning agent must produce very detailed, unambiguous plans
- Execution agent halts and escalates if plan is unclear
- Review agent catches issues that slip through

## Alternatives Considered

1. **Same model for all agents**: Simpler but expensive; Opus for execution would cost significantly more
1. **Haiku for planning too**: Cheaper but planning quality would suffer
1. **Sonnet for everything**: Middle ground but still expensive for execution volume
1. **Execution agent decides its own approach**: More flexible but unpredictable and expensive

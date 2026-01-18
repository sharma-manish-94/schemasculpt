# Architecture Decision Records (ADRs)

This directory contains finalized architectural decisions agreed upon by the AI collaboration (Claude Code + Gemini) and approved by the human.

## Purpose

ADRs provide a single source of truth for:
- **What** was decided
- **Why** it was decided (context, constraints, trade-offs)
- **Who** participated in the decision
- **When** it was finalized

## ADR Lifecycle

```
1. Gemini proposes in spec     → .ai_workspace/specs/SPEC_<feature>.md
2. Claude reviews/pushes back  → .ai_workspace/pushbacks/PUSHBACK_<feature>.md
3. Dispute resolved            → .ai_knowledge/disputes/resolution_log.md
4. Decision finalized          → .ai_knowledge/architecture/decisions/ADR-XXX_<title>.md
5. Human approves & commits
```

## Naming Convention

```
ADR-XXX_short_descriptive_title.md
```

Examples:
- `ADR-001_rate_limiting_approach.md`
- `ADR-002_jwt_vs_session_authentication.md`
- `ADR-003_analyzer_facade_pattern.md`

## ADR Statuses

| Status | Meaning |
|--------|---------|
| **PROPOSED** | Under discussion, not yet agreed |
| **ACCEPTED** | Agreed by AIs, awaiting human approval |
| **APPROVED** | Human approved and committed |
| **DEPRECATED** | Superseded by a newer ADR |
| **REJECTED** | Considered but not adopted |

## Reading ADRs

Each ADR contains:
1. **Title & Status** - What and current state
2. **Context** - Why this decision was needed
3. **Decision** - What was decided
4. **Participants** - Who contributed to the decision
5. **Options Considered** - Alternatives evaluated
6. **Rationale** - Why this option was chosen
7. **Consequences** - Trade-offs and implications
8. **References** - Related specs, pushbacks, patterns

## Quick Commands

```bash
# Source beast mode first
source .ai_knowledge/beast_mode_v3.sh

# Create new ADR
adr "Rate Limiting Approach"

# List all ADRs
adr_list

# View specific ADR
cat .ai_knowledge/architecture/decisions/ADR-001_*.md
```

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| - | (No decisions yet) | - | - |

---

*ADRs are created after AI consensus is reached and before human commit.*

# Pattern References

This directory contains project-specific standards that supplement the canonical patterns in `.claude/skills/`.

## Canonical Sources (DO NOT DUPLICATE)

| Pattern | Source |
|---------|--------|
| Analyzer Architecture | `.claude/skills/backend-api/patterns/analyzer-patterns.md` |
| Security Patterns | `.claude/skills/backend-api/patterns/security-patterns.md` |
| WebSocket Patterns | `.claude/skills/backend-api/patterns/websocket-session-patterns.md` |
| React Patterns | `.claude/skills/frontend-ui/patterns/react-patterns.md` |
| Zustand Patterns | `.claude/skills/frontend-ui/patterns/zustand-patterns.md` |
| FastAPI Patterns | `.claude/skills/ai-service/patterns/fastapi-patterns.md` |
| Code Review Standards | `.claude/skills/schemasculpt-code-reviewer/skill.md` |

## Files in This Directory

| File | Purpose |
|------|---------|
| `security_standards.md` | OWASP-aligned security checklist |
| `code_review_checklist.md` | Pre-commit review checklist |

## Adding New Standards

For patterns not covered in `.claude/skills/`, add them here with:
1. Clear title and scope
2. Rationale for the standard
3. Examples of correct implementation
4. Anti-patterns to avoid

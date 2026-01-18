# Tech Debt Register

Track known shortcuts so reviewers don't repeatedly flag them.

| ID | File/Area | Issue | Justification | Owner | Expiry |
|----|-----------|-------|---------------|-------|--------|
| TD-001 | ai_service | No test framework configured | MVP phase, manual testing | @manish | 2025-03-01 |
| TD-002 | WebSocket | No automatic reconnection | Planned for v2 | @manish | 2025-04-01 |

## Adding New Debt

Before merging code with known issues:
1. Add entry to this table with expiry date
2. Create tracking issue in project management tool
3. Get explicit approval from code owner

## Debt Entry Format

```
| TD-XXX | file/area | Brief issue description | Why this is acceptable | @owner | YYYY-MM-DD |
```

## Monthly Review Process

1. Review all entries with passed expiry dates
2. Either: resolve the debt, or extend with updated justification
3. Remove entries for resolved debt
4. Update LEARNING_GUIDE.md if debt revealed knowledge gaps

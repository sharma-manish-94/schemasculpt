# Code Review Checklist

## Logic & Correctness
- [ ] Edge cases handled (null, empty, boundary values)
- [ ] No off-by-one errors in loops/indices
- [ ] Async operations have proper error handling
- [ ] No race conditions in concurrent code
- [ ] Resource cleanup in finally/try-with-resources

## Security (OWASP Top 10)
- [ ] Input validated before use
- [ ] No hardcoded secrets
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevented (output encoding)
- [ ] Sensitive data not logged
- [ ] Authorization checked on all protected resources

## Performance
- [ ] No N+1 queries
- [ ] Appropriate use of caching
- [ ] No blocking calls in async context
- [ ] Connection/resource pools configured
- [ ] Pagination on list endpoints

## Maintainability
- [ ] Public APIs documented (Javadoc/JSDoc)
- [ ] Complex logic has comments explaining "why"
- [ ] No magic numbers—use named constants
- [ ] Error messages are actionable
- [ ] Follows project patterns in `.claude/skills/`

## Testing
- [ ] Unit tests for new public methods
- [ ] Edge cases tested
- [ ] Integration tests for new endpoints
- [ ] Tests are deterministic (no flaky tests)

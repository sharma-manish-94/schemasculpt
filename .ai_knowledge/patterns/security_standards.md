# Security Standards (OWASP-Aligned)

Reference: `.claude/skills/schemasculpt-code-reviewer/skill.md` for full checklist.

## Input Validation
- Validate at controller boundary using `@Valid` and Jakarta validation annotations
- Whitelist validation over blacklist
- File uploads: validate MIME type AND magic bytes
- Size limits on all inputs (configure in `application.yml`)

## Authentication & Authorization
- JWT tokens: ≤1 hour expiry for access tokens
- Refresh tokens: rotatable and revocable
- No sensitive data in JWT payload
- Rate limit auth endpoints: 5 attempts/minute/IP
- Authorization checks in service layer, not controller

## Data Protection
- PII encrypted at rest (database-level encryption)
- Secrets via environment variables or Spring Cloud Vault
- Logs must NOT contain: passwords, tokens, full credit cards, SSNs
- Use `@ToString.Exclude` on sensitive Lombok fields

## SQL/NoSQL
- Parameterized queries only (Spring Data handles this)
- No native queries with string concatenation
- Principle of least privilege for DB accounts

## Error Handling
- Never expose stack traces to clients
- Log full error internally with correlation ID
- Return generic message externally with same correlation ID
- Use `@ControllerAdvice` for global exception handling

## WebSocket Security
- Validate session on CONNECT
- Re-validate on sensitive operations
- Implement message size limits
- Clean up subscriptions on DISCONNECT

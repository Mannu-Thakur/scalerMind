# ADR-010: Authentication and Refresh Session Design

## Status
Accepted

## Context
ScalerMind needs account registration, role-protected API routes, and browser sessions that can renew short-lived access credentials while supporting logout and refresh-token theft detection.

## Decision
- Hash passwords with bcrypt at cost factor 12 and enforce a 12-character minimum and bcrypt's 72-byte input limit.
- Sign HS256 JWTs with an explicit issuer, audience, token type, subject, JTI, issue time, and expiry.
- Keep access tokens short-lived (15 minutes) and return them only in the JSON response for in-memory browser use.
- Store refresh tokens in HttpOnly, SameSite=Strict cookies for 7 days. Store only SHA-256 hashes in PostgreSQL.
- Rotate refresh tokens on use. Keep session family IDs and revoke the active family if a revoked token is presented again.
- Require a double-submit CSRF cookie/header pair for refresh and logout.
- Assign `learner` during public signup. Create administrators only through controlled provisioning.
- Require a configured secret of at least 32 characters and secure cookies when `APP_ENV=production`; development can use a per-process random key.

## Consequences
- Refresh credentials can be revoked and replay can be detected, at the cost of a database lookup on every refresh.
- Access tokens remain valid until their short expiry after logout; logout revokes refresh ability rather than maintaining a per-request access-token denylist.
- Local sessions are invalidated when the API restarts if no stable development signing key is configured.
- Production still needs HTTPS, origin/CORS policy, rate limiting, secret management, and security review.

## Alternatives considered
- Long-lived access tokens: simpler but increases the exposure window after token theft.
- Browser local storage for refresh tokens: easy to integrate but exposes the credential to JavaScript injection.
- Stateless refresh tokens: cannot reliably revoke sessions or detect replay without server-side state.

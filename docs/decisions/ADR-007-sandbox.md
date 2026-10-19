# ADR-007: Code Execution Sandbox Architecture

## Status
Accepted

## Context
Learner-submitted code must be executed to test correctness. This is the highest-security
concern in the platform. Untrusted code can be malicious, attempt to read secrets, or crash the process.

## Decision
Use subprocess-based execution with OS-level resource limits (RLIMIT_CPU, RLIMIT_AS)
and process group management. This runs in a dedicated Celery worker (never the API process).

## Security Controls Applied
1. CPU time limit: RLIMIT_CPU + SIGKILL after timeout+1s
2. Memory limit: RLIMIT_AS (256MB)
3. Output size limit: Truncate stdout/stderr at 64KB
4. Filesystem: No write access to host directories beyond /tmp
5. Process isolation: Separate Celery worker from API
6. User: Run as unprivileged user (uid 65534, nobody)
7. No network: Subprocess environment has no network access by default

## Migration Path
For higher security (production with real untrusted code):
→ Replace subprocess with nsjail (Linux namespaces + seccomp-BPF)
→ Or: gVisor-based Docker execution per submission

## Tradeoffs
- subprocess approach is sufficient for prototype/internship demo context
- Documented migration path to nsjail for production hardening
- Never run inside the API process

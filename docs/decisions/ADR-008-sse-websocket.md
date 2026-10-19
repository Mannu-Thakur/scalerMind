# ADR-008: SSE vs WebSocket for Streaming

## Status
Accepted

## Context
Real-time streaming is required for:
1. LLM token streaming (mentor chat responses)
2. Code review progress updates
3. Evaluation job progress

## Decision
Use Server-Sent Events (SSE) for all streaming use cases.

## Alternatives Considered
- WebSocket: Bidirectional, but all our streaming is unidirectional (server → client)
- WebSocket for LLM streaming: Adds connection state management complexity
- Long polling: Poor UX; unnecessary latency

## Rationale
SSE is simpler to implement and sufficient for all streaming use cases (server-to-client only).
HTTP/2 multiplexing means SSE does not consume extra connections.
Works with standard HTTP infrastructure (load balancers, proxies) when buffering is disabled.

## Implementation Note
Frontend uses fetch + ReadableStream (not the EventSource API) to support
POST requests and Authorization headers that EventSource cannot send.

## Tradeoffs
- SSE is unidirectional; if bidirectional real-time features are needed later, WebSocket is required
- Nginx proxy_buffering must be disabled for SSE to work

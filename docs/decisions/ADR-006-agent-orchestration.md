# ADR-006: Custom Agent Orchestration (No LangChain)

## Status
Accepted

## Context
The platform needs agentic workflows for code review, mentor chat, and analytics.
Framework options include LangChain, LlamaIndex, AutoGen, and custom orchestration.

## Decision
Implement custom bounded orchestrators in Python (no LangChain/LlamaIndex).

## Alternatives Considered
- LangChain: Heavy, opaque, frequently breaking changes, obscures what is actually happening
- LlamaIndex: Better for RAG, still adds heavy abstraction layer
- AutoGen: Designed for multi-agent conversations, overkill for bounded workflows
- Semantic Kernel: Microsoft-centric, complex abstraction

## Rationale
Each agent in ScalerMind has a fixed, bounded workflow (not open-ended reasoning).
Custom orchestration means:
- Every step is visible and debuggable
- No framework version conflicts
- No hidden prompt templates
- No magic that breaks between library versions
- Interviewer can understand every line of code

## Tradeoffs
- More code to write than using a framework
- Must implement retries, timeouts, tool validation manually
- Worth it: full control, full debuggability, no resume-keyword-only dependency

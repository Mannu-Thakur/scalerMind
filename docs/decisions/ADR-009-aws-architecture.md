# ADR-009: AWS Deployment Architecture

## Status
Accepted

## Context
The platform needs a production deployment architecture on AWS that is scalable,
manageable, and cost-effective for a startup-stage product.

## Decision
ECS Fargate for containers, RDS PostgreSQL for database, ElastiCache for Redis,
S3 for object storage, ALB for load balancing, CloudWatch for observability.

## Architecture

`
Internet → CloudFront → ALB → ECS Fargate (API tasks, Worker tasks)
ECS → RDS PostgreSQL (Multi-AZ in production)
ECS → ElastiCache Redis
ECS → S3 (documents, evaluation artifacts)
All services → CloudWatch Logs + Metrics
Secrets → AWS Secrets Manager (injected as env vars)
`

## Alternatives Considered
- EKS (Kubernetes): More powerful but significant operational overhead for a small team
- EC2 directly: No auto-scaling, manual patching burden
- Elastic Beanstalk: Less control, harder to configure worker processes
- Lambda: Cold start too slow for LLM requests; 15-min limit problematic for code review

## Rationale
ECS Fargate provides container orchestration without managing EC2 instances.
Fargate auto-scaling handles traffic spikes.
RDS Multi-AZ provides high availability for the primary data store.
All services are fully managed, reducing operational overhead.

## Tradeoffs
- Fargate is more expensive per vCPU/GB than EC2
- ECS is less flexible than Kubernetes for complex scheduling
- Mitigation: Start with small task sizes; scale up only as needed

# RobCo Forge — Steering Rules

## Architecture
- All compute delivery via AWS WorkSpaces Personal + Applications — NO EC2 instances
- All streaming via WSP — PCoIP is FORBIDDEN everywhere
- Support both Windows and Linux operating systems for WorkSpaces
- All WorkSpaces MUST be domain-joined to RobCo Active Directory
- User volumes stored on Amazon FSx for NetApp ONTAP (NOT EFS)
- Lucy chatbot is a first-class interface alongside portal and CLI
- All infrastructure defined as IaC (Terraform + CDK)
- Every API endpoint must have OpenAPI documentation
- All services emit structured logs and metrics
- Zero trust networking: no implicit trust between components

## Code Standards
- TypeScript strict mode for frontend and CLI
- Python type hints for backend services
- 80% minimum test coverage for business logic
- All secrets via AWS Secrets Manager — never hardcoded
- Conventional commits required

## Security First
- Every PR must pass SAST/DAST scans
- No cloud resource without encryption at rest and in transit
- IAM policies follow least-privilege principle
- All user actions produce audit events (including Lucy conversations)
- WorkSpaces must have clipboard, USB, drive, printing disabled
- Screen watermark mandatory on all sessions

## Lucy Guidelines
- Lucy system prompt changes require review + eval test pass
- All Lucy tool calls go through the Forge API (no direct AWS API calls from Lucy)
- Destructive actions always require user confirmation
- Lucy respects RBAC — never bypasses role permissions
- Rate limit: max 5 provisioning actions per user per hour via Lucy

## Development Flow
- Write tests before implementation (TDD)
- Each task must include verification steps
- Infrastructure changes require plan output review before apply
- Lucy prompt changes require conversation corpus evaluation before deploy
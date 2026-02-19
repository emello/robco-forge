# Implementation Plan: RobCo Forge

## Overview

This implementation plan breaks down the RobCo Forge platform into discrete, manageable tasks. The platform consists of six major components:

1. **Infrastructure Foundation** - AWS resources, networking, Kubernetes cluster
2. **Core API Services** - FastAPI backend, authentication, RBAC
3. **Provisioning Service** - WorkSpace lifecycle management, pre-warmed pools
4. **Lucy AI Service** - Anthropic Claude integration, conversational interface
5. **Cost Engine** - Real-time cost tracking, budget enforcement, optimization
6. **User Interfaces** - Web portal (React/Next.js), CLI (TypeScript), Slack integration

The implementation follows a bottom-up approach: infrastructure first, then core services, then user-facing features. Each task includes specific requirements references for traceability.

## Tasks

### Phase 1: Infrastructure Foundation

- [x] 1. Set up AWS infrastructure with Terraform
  - [x] 1.1 Create Terraform module structure
    - Create modules for: workspaces, networking, eks, rds, efs, monitoring
    - Set up environment directories: dev, staging, production
    - Configure remote state backend (S3 + DynamoDB)
    - _Requirements: 25.1, 25.3_
  
  - [x] 1.2 Implement networking module
    - Create isolated VPCs for WorkSpaces (no direct internet access)
    - Create private subnets across 3 availability zones
    - Set up NAT gateway with egress allowlist
    - Configure VPC endpoints for S3, Secrets Manager, FSx
    - Create security groups with least-privilege rules
    - _Requirements: 9.1, 9.2, 9.3, 9.5_
  
  - [x] 1.3 Implement EKS cluster module
    - Create EKS cluster spanning 3 availability zones
    - Configure private API endpoint
    - Set up node groups in private subnets
    - Configure IAM roles for service accounts (IRSA)
    - Enable cluster logging to CloudWatch
    - _Requirements: 24.1, 24.3_
  
  - [x] 1.4 Implement RDS PostgreSQL module
    - Create RDS PostgreSQL 15 instance with Multi-AZ
    - Enable encryption at rest (AES-256)
    - Configure automated backups (daily, 30-day retention)
    - Set up read replica for cost queries
    - Configure connection pooling (PgBouncer)
    - Create security group allowing only EKS pods
    - _Requirements: 10.3_
  
  - [x] 1.5 Implement FSx ONTAP module for user volumes
    - Create FSx for NetApp ONTAP filesystem
    - Enable encryption at rest (AES-256)
    - Configure automated backups (daily, 30-day retention)
    - Enable deduplication and compression
    - Set up SVM for user volumes
    - _Requirements: 4.4, 4.5, 20.1, 20.3_
  
  - [x] 1.6 Implement WorkSpaces directory module
    - Create AWS WorkSpaces directory
    - Configure Active Directory integration
    - Disable PCoIP at directory level (WSP-only)
    - Set up domain join configuration
    - Configure Group Policies for data exfiltration prevention
    - _Requirements: 3.1, 3.2, 4A.1, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 1.7 Implement monitoring module
    - Set up CloudWatch log groups with retention policies
    - Configure Prometheus deployment on EKS
    - Set up Grafana deployment on EKS
    - Create CloudWatch alarms for critical metrics
    - Configure SNS topics for alerts
    - _Requirements: 23.1, 23.2, 23.3_

- [x] 2. Deploy Kubernetes infrastructure with AWS CDK
  - [x] 2.1 Create CDK project structure
    - Initialize CDK TypeScript project
    - Create stacks for: API, Lucy, Cost Engine, monitoring
    - Configure CDK context for environments
    - _Requirements: 25.2, 25.3_
  
  - [x] 2.2 Implement namespace and RBAC configuration
    - Create namespaces: forge-api, forge-system, forge-workers
    - Configure service accounts with IRSA
    - Set up RBAC roles and bindings
    - Configure network policies
    - _Requirements: 8.3, 8.4_
  
  - [x] 2.3 Implement secrets management
    - Create Kubernetes secrets from AWS Secrets Manager
    - Set up External Secrets Operator
    - Configure automatic secret rotation
    - _Requirements: 21.1, 21.4_

- [x] 3. Checkpoint - Infrastructure validation
  - Verify all Terraform modules deploy successfully
  - Verify EKS cluster is healthy
  - Verify RDS and FSx are accessible from EKS
  - Verify WorkSpaces directory is configured correctly
  - Ensure all tests pass, ask the user if questions arise.


### Phase 2: Core API and Data Layer

- [x] 4. Implement database models and migrations
  - [x] 4.1 Create SQLAlchemy models
    - Implement WorkSpace model with all fields and relationships
    - Implement Blueprint model with version control
    - Implement CostRecord model with aggregation support
    - Implement UserBudget model with threshold tracking
    - Implement AuditLog model with tamper-evident storage
    - _Requirements: 1.1, 2.1, 10.1, 10.2, 11.1, 12.1_
  
  - [ ]* 4.2 Write property test for data models
    - **Property 6: Blueprint Version Immutability**
    - **Validates: Requirements 2.3**
  
  - [x] 4.3 Create Alembic migrations
    - Set up Alembic for database migrations
    - Create initial migration for all tables
    - Add indexes for performance (user_id, team_id, timestamp)
    - Configure partitioning for audit_logs table (by month)
    - _Requirements: 10.3_
  
  - [ ]* 4.4 Write unit tests for database models
    - Test model creation and validation
    - Test relationships and cascading deletes
    - Test enum constraints
    - _Requirements: 1.1, 2.1, 10.1_

- [x] 5. Implement authentication and authorization
  - [x] 5.1 Implement Okta SSO integration
    - Set up SAML 2.0 authentication with Okta
    - Implement SSO login endpoint
    - Implement SSO callback handler
    - Generate and validate JWT tokens
    - _Requirements: 8.1, 8.2_
  
  - [x] 5.2 Implement RBAC system
    - Define role hierarchy (engineer, team_lead, contractor, admin)
    - Implement permission checking middleware
    - Create role assignment API
    - Implement time-bound credentials for contractors
    - _Requirements: 8.3, 8.4, 8.5, 8.6_
  
  - [ ]* 5.3 Write property test for RBAC enforcement
    - **Property 29: Authorization Verification**
    - **Validates: Requirements 8.4, 22.3**
  
  - [ ]* 5.4 Write property test for contractor credentials
    - **Property 30: Contractor Credential Expiration**
    - **Validates: Requirements 8.5**
  
  - [ ]* 5.5 Write unit tests for authentication
    - Test SSO login flow
    - Test MFA requirement
    - Test JWT token generation and validation
    - Test expired token handling
    - _Requirements: 8.1, 8.2_

- [x] 6. Implement Forge API core endpoints
  - [x] 6.1 Create FastAPI application structure
    - Set up FastAPI app with OpenAPI documentation
    - Configure CORS and security headers
    - Implement health check and readiness endpoints
    - Set up structured logging (JSON format)
    - Configure OpenTelemetry for distributed tracing
    - _Requirements: 23.1, 23.6_
  
  - [x] 6.2 Implement WorkSpace management endpoints
    - POST /api/v1/workspaces - Provision WorkSpace
    - GET /api/v1/workspaces - List WorkSpaces
    - GET /api/v1/workspaces/{id} - Get WorkSpace details
    - POST /api/v1/workspaces/{id}/start - Start WorkSpace
    - POST /api/v1/workspaces/{id}/stop - Stop WorkSpace
    - DELETE /api/v1/workspaces/{id} - Terminate WorkSpace
    - _Requirements: 1.1, 1.7, 1.9_
  
  - [x] 6.3 Implement Blueprint management endpoints
    - GET /api/v1/blueprints - List Blueprints
    - POST /api/v1/blueprints - Create Blueprint
    - GET /api/v1/blueprints/{id} - Get Blueprint details
    - PUT /api/v1/blueprints/{id} - Update Blueprint
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 6.4 Implement cost endpoints
    - GET /api/v1/costs - Get cost data
    - GET /api/v1/costs/recommendations - Get optimization recommendations
    - GET /api/v1/costs/reports - Generate cost reports
    - _Requirements: 11.1, 11.2, 13.5, 16.1, 16.2_
  
  - [ ]* 6.5 Write unit tests for API endpoints
    - Test request validation
    - Test error responses
    - Test authentication requirements
    - Test RBAC enforcement
    - _Requirements: 8.3, 8.4_

- [x] 7. Implement audit logging system
  - [x] 7.1 Create audit logging middleware
    - Capture all API requests
    - Extract user identity, action, resource, result
    - Store in tamper-evident format
    - _Requirements: 10.1, 10.2_
  
  - [ ]* 7.2 Write property test for audit logging
    - **Property 37: Comprehensive Audit Logging**
    - **Validates: Requirements 10.1**
  
  - [ ]* 7.3 Write property test for audit log completeness
    - **Property 38: Audit Log Completeness**
    - **Validates: Requirements 10.2**
  
  - [ ]* 7.4 Write unit tests for audit logging
    - Test log entry creation
    - Test log field completeness
    - Test tamper-evident storage
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 8. Checkpoint - Core API validation
  - Verify all API endpoints are functional
  - Verify authentication and RBAC work correctly
  - Verify audit logging captures all actions
  - Ensure all tests pass, ask the user if questions arise.


### Phase 3: Provisioning Service

- [x] 9. Implement WorkSpace provisioning core
  - [x] 9.1 Create AWS WorkSpaces API client
    - Implement wrapper for AWS WorkSpaces API
    - Add retry logic with exponential backoff
    - Implement circuit breaker pattern
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 9.2 Implement region selection logic
    - Implement geographic location detection from IP
    - Calculate latency to all available regions
    - Select region with lowest latency
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 9.3 Write property test for region selection
    - **Property 9: Geographic Location Detection**
    - **Property 10: Optimal Region Selection**
    - **Property 11: Region Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  
  - [x] 9.4 Implement WorkSpace configuration
    - Configure WSP-only streaming (disable PCoIP)
    - Apply security Group Policies (disable clipboard, USB, drive mapping, printing)
    - Enable screen watermarking
    - _Requirements: 3.1, 3.2, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [ ]* 9.5 Write property test for WSP-only configuration
    - **Property 8: WSP-Only Configuration**
    - **Validates: Requirements 3.1**
  
  - [ ]* 9.6 Write property test for screen watermark
    - **Property 27: Screen Watermark Presence and Persistence**
    - **Validates: Requirements 7.6, 7.7**

- [x] 10. Implement Active Directory domain join
  - [x] 10.1 Create domain join service
    - Implement domain join logic with retry (up to 3 attempts)
    - Track domain join status in database
    - Handle domain join failures gracefully
    - _Requirements: 4A.1, 4A.2, 4A.3, 4A.4, 4A.5_
  
  - [ ]* 10.2 Write unit tests for domain join
    - Test successful domain join
    - Test retry logic on failure
    - Test failure after max retries
    - _Requirements: 4A.5_

- [x] 11. Implement user volume management
  - [x] 11.1 Create FSx ONTAP volume service
    - Implement user volume creation on FSx
    - Implement volume attachment to WorkSpaces
    - Implement volume persistence on disconnect
    - _Requirements: 4.4, 4.5_
  
  - [ ]* 11.2 Write property test for user volume attachment
    - **Property 12: User Volume Attachment**
    - **Property 13: User Volume Persistence**
    - **Validates: Requirements 4.4, 4.5**
  
  - [x] 11.3 Implement dotfile synchronization
    - Sync dotfiles from user volume to WorkSpace on launch
    - Persist dotfile changes back to user volume
    - Support shell configs, editor configs, Git config
    - Apply dotfiles within 30 seconds of launch
    - _Requirements: 20.1, 20.2, 20.3, 20.4_
  
  - [ ]* 11.4 Write property test for dotfile sync
    - **Property 67: Dotfile Synchronization**
    - **Property 68: Dotfile Persistence**
    - **Validates: Requirements 20.1, 20.3**

- [x] 12. Implement secrets management integration
  - [x] 12.1 Create secrets injection service
    - Fetch secrets from AWS Secrets Manager based on RBAC
    - Inject secrets as environment variables at launch
    - Implement secret rotation handling
    - Update environment variables in running WorkSpaces within 5 minutes
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_
  
  - [ ]* 12.2 Write property test for secret injection
    - **Property 69: Secret Injection at Launch**
    - **Property 70: Secret Access Scoping**
    - **Validates: Requirements 21.2, 21.3**
  
  - [ ]* 12.3 Write property test for secret rotation
    - **Property 71: Secret Rotation**
    - **Property 72: Secret Rotation Propagation**
    - **Validates: Requirements 21.4, 21.5**

- [x] 13. Implement pre-warmed WorkSpace pools
  - [x] 13.1 Create pool management service
    - Maintain pools of pre-provisioned WorkSpaces per blueprint
    - Configure pool size (min 5, max 20)
    - Implement pool replenishment logic
    - Adjust pool size based on demand patterns
    - _Requirements: 19.1, 19.4, 19.5_
  
  - [x] 13.2 Implement pool assignment logic
    - Assign pre-warmed WorkSpace when available
    - Customize WorkSpace with user volume and config
    - Fall back to on-demand provisioning if pool empty
    - _Requirements: 19.2, 19.3_
  
  - [ ]* 13.3 Write property test for pre-warmed pools
    - **Property 63: Pre-Warmed Pool Maintenance**
    - **Property 64: Pre-Warmed Pool Assignment**
    - **Property 65: Pre-Warmed Workspace Customization**
    - **Property 66: Pool Replenishment**
    - **Validates: Requirements 19.1, 19.2, 19.3, 19.4**

- [x] 14. Implement WorkSpace lifecycle management
  - [x] 14.1 Create idle timeout service
    - Monitor WorkSpace sessions for activity
    - Auto-stop WorkSpaces after configured idle timeout
    - _Requirements: 1.7, 14.1_
  
  - [ ]* 14.2 Write property test for idle timeout
    - **Property 3: Idle Timeout Enforcement**
    - **Validates: Requirements 1.7**
  
  - [x] 14.3 Create maximum lifetime service
    - Track WorkSpace age
    - Auto-terminate WorkSpaces at maximum lifetime
    - _Requirements: 1.9_
  
  - [ ]* 14.4 Write property test for maximum lifetime
    - **Property 4: Maximum Lifetime Enforcement**
    - **Validates: Requirements 1.9**
  
  - [x] 14.5 Create stale workspace cleanup service
    - Flag WorkSpaces stopped for 30 days as stale
    - Send notification to owner
    - Terminate after 7 days if still unused
    - Respect "keep alive" flag
    - _Requirements: 14.2, 14.3, 14.4, 14.5_
  
  - [ ]* 14.6 Write property test for stale workspace cleanup
    - **Property 48: Stale Workspace Detection**
    - **Property 49: Stale Workspace Notification**
    - **Property 50: Stale Workspace Termination**
    - **Property 51: Keep-Alive Protection**
    - **Validates: Requirements 14.2, 14.3, 14.4, 14.5**

- [x] 15. Implement provisioning time monitoring
  - [x] 15.1 Add provisioning time tracking
    - Track time from request to AVAILABLE state
    - Emit metrics to CloudWatch and Prometheus
    - Trigger alert if provisioning exceeds 5 minutes
    - _Requirements: 1.1, 23.1, 23.4_
  
  - [ ]* 15.2 Write property test for provisioning time bound
    - **Property 1: Provisioning Time Bound**
    - **Validates: Requirements 1.1**

- [x] 16. Checkpoint - Provisioning service validation
  - Verify WorkSpaces provision successfully in all regions
  - Verify domain join works correctly
  - Verify user volumes attach and persist
  - Verify pre-warmed pools function correctly
  - Ensure all tests pass, ask the user if questions arise.


### Phase 4: Cost Engine

- [x] 17. Implement cost calculation engine
  - [x] 17.1 Create cost calculator service
    - Implement cost calculation for all bundle types
    - Calculate compute, storage, and data transfer costs
    - Track costs in real-time (5-minute latency)
    - _Requirements: 11.1, 11.4_
  
  - [ ]* 17.2 Write property test for cost calculation
    - **Property 39: Real-Time Cost Tracking**
    - **Validates: Requirements 11.1, 11.4**
  
  - [x] 17.3 Implement cost aggregation
    - Aggregate costs by WorkSpace, user, team, project
    - Support time period filtering (daily, weekly, monthly, custom)
    - _Requirements: 11.2, 11.5_
  
  - [ ]* 17.4 Write unit tests for cost calculation
    - Test cost calculation for each bundle type
    - Test storage cost calculation
    - Test data transfer cost calculation
    - Test cost aggregation
    - _Requirements: 11.1, 11.4_

- [x] 18. Implement budget enforcement
  - [x] 18.1 Create budget tracking service
    - Track spending against budgets (user, team, project)
    - Send warning at 80% threshold
    - Block provisioning at 100% threshold
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [ ]* 18.2 Write property test for budget warnings
    - **Property 40: Budget Warning at 80%**
    - **Validates: Requirements 12.2**
  
  - [ ]* 18.3 Write property test for budget hard limit
    - **Property 41: Budget Hard Limit at 100%**
    - **Validates: Requirements 12.3**
  
  - [ ]* 18.4 Write property test for multi-interface budget enforcement
    - **Property 42: Multi-Interface Budget Enforcement**
    - **Validates: Requirements 12.4, 12.5, 12.6, 22.4**
  
  - [x] 18.5 Integrate budget checks into provisioning flow
    - Check budget before provisioning in API
    - Check budget before provisioning in Lucy
    - Check budget before provisioning in CLI
    - Return clear error messages on budget exceeded
    - _Requirements: 12.4, 12.5, 12.6_

- [x] 19. Implement utilization analysis and recommendations
  - [x] 19.1 Create utilization analyzer service
    - Collect CloudWatch metrics (CPU, memory, session hours)
    - Analyze utilization over 14-day period
    - _Requirements: 13.1_
  
  - [x] 19.2 Implement right-sizing recommendations
    - Recommend downgrade for CPU < 20% over 14 days
    - Recommend upgrade for CPU > 80% over 14 days
    - Calculate estimated cost savings/increases
    - _Requirements: 13.2, 13.3, 13.4_
  
  - [ ]* 19.3 Write property test for utilization analysis
    - **Property 43: Utilization Analysis Period**
    - **Property 44: Downgrade Recommendation for Low Utilization**
    - **Property 45: Upgrade Recommendation for High Utilization**
    - **Property 46: Cost Impact Calculation**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4**
  
  - [x] 19.4 Implement billing mode recommendations
    - Track usage hours per month
    - Recommend monthly billing for > 80 hours/month
    - Recommend hourly billing for < 80 hours/month
    - Calculate cost difference between modes
    - _Requirements: 15.1, 15.2, 15.3, 15.4_
  
  - [ ]* 19.5 Write property test for billing mode recommendations
    - **Property 52: Usage Hours Tracking**
    - **Property 53: Monthly Billing Recommendation**
    - **Property 54: Hourly Billing Recommendation**
    - **Property 55: Billing Mode Cost Comparison**
    - **Validates: Requirements 15.1, 15.2, 15.3, 15.4**

- [x] 20. Implement cost reporting
  - [x] 20.1 Create cost report generator
    - Generate monthly reports by team, project, cost center
    - Include total costs, breakdown by bundle type, storage, data transfer
    - Support CSV and PDF export formats
    - _Requirements: 16.1, 16.2, 16.3_
  
  - [ ]* 20.2 Write property test for cost reports
    - **Property 56: Monthly Cost Report Generation**
    - **Property 57: Cost Report Completeness**
    - **Validates: Requirements 16.1, 16.2**
  
  - [x] 20.3 Implement cost allocation tags
    - Support custom cost allocation tags
    - Allow tag assignment during provisioning
    - Include tags in cost reports
    - _Requirements: 16.4, 16.5_
  
  - [ ]* 20.4 Write property test for cost allocation tags
    - **Property 58: Cost Allocation Tag Assignment**
    - **Validates: Requirements 16.5**

- [x] 21. Checkpoint - Cost engine validation
  - Verify cost calculations are accurate
  - Verify budget enforcement blocks provisioning at 100%
  - Verify recommendations are generated correctly
  - Ensure all tests pass, ask the user if questions arise.


### Phase 5: Lucy AI Service

- [ ] 22. Implement Lucy AI core infrastructure
  - [x] 22.1 Set up Anthropic Claude integration
    - Configure Claude API client (via AWS Bedrock or direct API)
    - Implement prompt caching for cost optimization
    - Set up conversation context storage in Redis (30-minute TTL)
    - _Requirements: 5.1, 6.1, 6.2_
  
  - [x] 22.2 Create conversation context manager
    - Implement context storage and retrieval
    - Implement 30-minute TTL expiration
    - Track conversation history and intent
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 22.3 Write property test for Lucy context retention
    - **Property 20: Lucy Context Retention**
    - **Property 21: Lucy Context Expiration**
    - **Validates: Requirements 6.1, 6.2**

- [ ] 23. Implement Lucy tool definitions
  - [x] 23.1 Create tool executor framework
    - Define tool interface for Claude function calling
    - Implement tool execution with error handling
    - Add rate limiting (5 provisions per user per hour)
    - _Requirements: 5.4_
  
  - [x] 23.2 Implement workspace management tools
    - provision_workspace tool (calls Forge API)
    - list_workspaces tool (calls Forge API)
    - start_workspace tool (calls Forge API)
    - stop_workspace tool (calls Forge API, requires confirmation)
    - terminate_workspace tool (calls Forge API, requires confirmation)
    - _Requirements: 5.4, 5.5_
  
  - [ ]* 23.3 Write property test for Lucy provisioning authorization
    - **Property 15: Lucy Provisioning with Authorization**
    - **Validates: Requirements 5.4**
  
  - [ ]* 23.4 Write property test for Lucy workspace management
    - **Property 16: Lucy Workspace Management with Authorization**
    - **Validates: Requirements 5.5**
  
  - [ ]* 23.5 Write property test for Lucy rate limiting
    - **Property 26: Lucy Rate Limiting**
    - **Validates: Requirements 5.4**
  
  - [x] 23.3 Implement cost and diagnostic tools
    - get_cost_summary tool (calls Cost Engine)
    - get_cost_recommendations tool (calls Cost Engine)
    - run_diagnostics tool (calls Forge API)
    - check_budget tool (calls Cost Engine)
    - _Requirements: 5.6, 5.7_
  
  - [ ]* 23.4 Write property test for Lucy cost integration
    - **Property 17: Lucy Cost Query Integration**
    - **Property 47: Lucy Cost Optimization Integration**
    - **Validates: Requirements 5.6, 13.6**
  
  - [ ]* 23.5 Write property test for Lucy diagnostics
    - **Property 18: Lucy Diagnostic Execution**
    - **Validates: Requirements 5.7**
  
  - [x] 23.6 Implement support and routing tools
    - create_support_ticket tool (calls Forge API)
    - Implement fallback routing for unfulfillable requests
    - _Requirements: 5.8_
  
  - [ ]* 23.7 Write property test for Lucy fallback routing
    - **Property 19: Lucy Fallback Routing**
    - **Validates: Requirements 5.8**

- [ ] 24. Implement Lucy system prompt and personality
  - [x] 24.1 Create Lucy system prompt
    - Define Lucy's role and capabilities
    - Specify security constraints (RBAC, budget, confirmation)
    - Define response style (friendly, professional, concise)
    - Add theme-aware personality variants
    - _Requirements: 5.1, 6.3, 6.4, 6.5_
  
  - [x] 24.2 Implement intent recognition
    - Parse user requests to identify intent
    - Map intents to appropriate tools
    - Handle ambiguous requests
    - _Requirements: 5.3, 5.4, 5.5_
  
  - [ ]* 24.3 Write property test for Lucy RBAC enforcement
    - **Property 22: Lucy RBAC Enforcement**
    - **Validates: Requirements 6.3**
  
  - [ ]* 24.4 Write property test for Lucy budget denial
    - **Property 23: Lucy Budget Denial**
    - **Validates: Requirements 6.4**
  
  - [ ]* 24.5 Write property test for Lucy cost warnings
    - **Property 24: Lucy Cost Warnings**
    - **Validates: Requirements 6.6**

- [ ] 25. Implement Lucy audit logging
  - [x] 25.1 Add audit logging for all Lucy actions
    - Log every tool execution
    - Include user identity, action, timestamp
    - Store in audit_logs table
    - _Requirements: 6.7_
  
  - [ ]* 25.2 Write property test for Lucy audit logging
    - **Property 25: Lucy Audit Logging**
    - **Validates: Requirements 6.7**

- [ ] 26. Implement Lucy API endpoints
  - [x] 26.1 Create Lucy chat endpoint
    - POST /api/v1/lucy/chat - Send message to Lucy
    - GET /api/v1/lucy/context - Get conversation context
    - DELETE /api/v1/lucy/context - Clear conversation context
    - _Requirements: 5.2_
  
  - [ ]* 26.2 Write unit tests for Lucy endpoints
    - Test message handling
    - Test context management
    - Test error handling
    - _Requirements: 5.2_

- [ ] 27. Implement Lucy evaluation testing
  - [x] 27.1 Create conversation corpus for testing
    - Create test cases for provisioning requests
    - Create test cases for cost queries
    - Create test cases for error scenarios
    - Create test cases for RBAC denials
    - _Requirements: 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 27.2 Write evaluation tests for Lucy
    - Test intent recognition accuracy
    - Test tool selection accuracy
    - Test response quality
    - Require > 95% success rate for prompt changes
    - _Requirements: 5.1, 5.2_

- [x] 28. Checkpoint - Lucy AI validation
  - Verify Lucy can provision WorkSpaces correctly
  - Verify Lucy enforces RBAC and budget limits
  - Verify Lucy provides accurate cost information
  - Verify conversation context works correctly
  - Ensure all tests pass, ask the user if questions arise.


### Phase 6: Forge CLI

- [ ] 29. Implement CLI core framework
  - [x] 29.1 Set up TypeScript CLI project
    - Initialize TypeScript project with strict mode
    - Set up Commander.js for CLI framework
    - Configure build and packaging
    - _Requirements: 17.1_
  
  - [x] 29.2 Create Forge API client SDK
    - Implement TypeScript client for Forge API
    - Add authentication (JWT token management)
    - Implement retry logic and error handling
    - _Requirements: 17.1_
  
  - [ ]* 29.3 Write unit tests for API client
    - Test authentication
    - Test request/response handling
    - Test error handling
    - _Requirements: 17.1_

- [ ] 30. Implement CLI commands
  - [x] 30.1 Implement workspace management commands
    - forge launch - Provision WorkSpace
    - forge list - List WorkSpaces
    - forge describe - Get WorkSpace details
    - forge start - Start WorkSpace
    - forge stop - Stop WorkSpace
    - forge terminate - Terminate WorkSpace
    - _Requirements: 17.2, 17.3, 17.4_
  
  - [ ]* 30.2 Write property test for CLI provisioning
    - **Property 59: CLI Provisioning**
    - **Validates: Requirements 17.3**
  
  - [x] 30.3 Implement cost commands
    - forge costs - View cost data
    - forge costs recommendations - View optimization recommendations
    - _Requirements: 17.5_
  
  - [x] 30.4 Implement Lucy integration command
    - forge ask - Send question to Lucy
    - _Requirements: 17.6_
  
  - [ ]* 30.5 Write property test for CLI Lucy integration
    - **Property 60: CLI Lucy Integration**
    - **Validates: Requirements 17.6**
  
  - [x] 30.6 Implement configuration commands
    - forge config set - Set configuration values
    - forge config get - Get configuration values
    - forge config list - List all configuration
    - _Requirements: 17.1_

- [ ] 31. Implement CLI output formatting
  - [x] 31.1 Add table formatting for list commands
    - Format workspace list as table
    - Format cost data as table
    - Support JSON output format (--json flag)
    - _Requirements: 17.4_
  
  - [x] 31.2 Add color and styling
    - Use colors for status indicators
    - Add icons for visual clarity
    - Support --no-color flag
    - _Requirements: 17.1_

- [ ] 32. Implement CLI error handling
  - [x] 32.1 Add user-friendly error messages
    - Map API errors to CLI error messages
    - Include suggested actions in errors
    - Provide relevant command examples
    - _Requirements: 22.5_
  
  - [ ]* 32.2 Write unit tests for error handling
    - Test error message formatting
    - Test error code mapping
    - Test suggested actions
    - _Requirements: 22.5_

- [x] 33. Checkpoint - CLI validation
  - Verify all CLI commands work correctly
  - Verify CLI enforces RBAC and budget limits
  - Verify error messages are clear and helpful
  - Ensure all tests pass, ask the user if questions arise.


### Phase 7: Forge Portal (Web UI)

- [ ] 34. Set up React/Next.js project
  - [x] 34.1 Initialize Next.js 14 project
    - Set up Next.js with App Router
    - Configure TypeScript with strict mode
    - Set up Tailwind CSS
    - Configure ESLint and Prettier
    - _Requirements: 22.1_
  
  - [x] 34.2 Set up data fetching with TanStack Query
    - Configure TanStack Query client
    - Set up API client with authentication
    - Implement WebSocket connection for real-time updates
    - _Requirements: 22.2_
  
  - [x] 34.3 Implement theme system
    - Create theme context (modern vs. retro)
    - Implement theme switching
    - Persist theme preference per user
    - _Requirements: 22.1_

- [ ] 35. Implement authentication and routing
  - [x] 35.1 Create authentication flow
    - Implement SSO login page
    - Implement SSO callback handler
    - Store JWT token securely
    - Implement protected routes
    - _Requirements: 8.1, 8.2_
  
  - [x] 35.2 Create navigation and layout
    - Implement main navigation
    - Create page layouts for both themes
    - Add user profile menu
    - _Requirements: 22.1_

- [ ] 36. Implement Dashboard page
  - [x] 36.1 Create dashboard components (modern theme)
    - WorkSpace quick actions card
    - Cost summary card
    - Active WorkSpaces card
    - Budget status card
    - WorkSpace list with status indicators
    - Cost recommendations panel
    - _Requirements: 11.2, 11.3, 13.5_
  
  - [x] 36.2 Create dashboard components (retro theme)
    - Terminal-style dashboard with scanlines
    - ASCII art and retro styling
    - Monochrome green/amber color scheme
    - Bitmap fonts (VT323, Share Tech Mono)
    - _Requirements: 22.1_
  
  - [ ]* 36.3 Write unit tests for dashboard
    - Test data loading
    - Test quick actions
    - Test theme switching
    - _Requirements: 11.2_

- [ ] 37. Implement WorkSpaces management page
  - [x] 37.1 Create WorkSpace list view
    - Display all user WorkSpaces
    - Show status, bundle type, region, cost
    - Add filtering and sorting
    - _Requirements: 1.1_
  
  - [x] 37.2 Create WorkSpace provisioning modal
    - Bundle type selector
    - Blueprint selector
    - Operating system selector (Windows/Linux)
    - Cost estimate display
    - Implement for both themes
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 37.3 Implement WorkSpace actions
    - Start, stop, terminate buttons
    - Connection URL display
    - WorkSpace details view
    - _Requirements: 1.7, 1.9_
  
  - [ ]* 37.4 Write integration tests for WorkSpace management
    - Test provisioning flow
    - Test start/stop actions
    - Test budget enforcement in UI
    - _Requirements: 1.1, 12.6_

- [ ] 38. Implement Blueprints page
  - [x] 38.1 Create Blueprint list view
    - Display available Blueprints
    - Filter by team membership
    - Show Blueprint details (software, version)
    - _Requirements: 2.4, 2.5_
  
  - [x] 38.2 Create Blueprint creation form
    - Name, description, OS selection
    - Software manifest input
    - Team access control
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 38.3 Write property test for Blueprint filtering
    - **Property 7: Blueprint Filtering by Team Membership**
    - **Validates: Requirements 2.5**

- [ ] 39. Implement Cost dashboard page
  - [x] 39.1 Create cost visualization components
    - Cost summary cards (total, by team, by project)
    - Cost trend charts (daily, weekly, monthly)
    - Cost breakdown by bundle type
    - Time period selector
    - _Requirements: 11.2, 11.3, 11.5_
  
  - [x] 39.2 Create cost recommendations panel
    - Display right-sizing recommendations
    - Display billing mode recommendations
    - Show estimated savings
    - _Requirements: 13.5, 15.5_
  
  - [x] 39.3 Create budget status display
    - Show current spend vs. budget
    - Display warning at 80% threshold
    - Block provisioning UI at 100% threshold
    - _Requirements: 12.2, 12.3, 12.6_
  
  - [ ]* 39.4 Write unit tests for cost dashboard
    - Test cost data display
    - Test budget warnings
    - Test provisioning block at 100%
    - _Requirements: 11.2, 12.6_

- [ ] 40. Implement Lucy chat widget
  - [x] 40.1 Create chat interface (modern theme)
    - Chat message list
    - Input field with send button
    - Typing indicators
    - Error handling
    - _Requirements: 5.2_
  
  - [x] 40.2 Create chat interface (retro theme)
    - Terminal-style chat with scanlines
    - Command prompt styling
    - Cursor blink animation
    - Retro sound effects (optional)
    - _Requirements: 5.2_
  
  - [x] 40.3 Implement chat functionality
    - Send messages to Lucy API
    - Display Lucy responses
    - Handle tool execution feedback
    - Show cost warnings proactively
    - _Requirements: 5.2, 6.6_
  
  - [ ]* 40.4 Write integration tests for Lucy chat
    - Test message sending
    - Test response display
    - Test error handling
    - _Requirements: 5.2_

- [ ] 41. Implement Settings page
  - [x] 41.1 Create user preferences
    - Theme selection (modern vs. retro)
    - Default bundle type
    - Default region
    - Notification preferences
    - _Requirements: 22.1_
  
  - [x] 41.2 Create team management (for team leads)
    - View team members
    - Manage team budgets
    - View team costs
    - _Requirements: 12.1_

- [ ] 42. Implement accessibility features
  - [x] 42.1 Add keyboard navigation
    - Ensure all interactive elements are keyboard accessible
    - Add focus indicators
    - Implement keyboard shortcuts
    - _Requirements: 22.1_
  
  - [x] 42.2 Add screen reader support
    - Add ARIA labels
    - Add alt text for images
    - Ensure semantic HTML
    - _Requirements: 22.1_
  
  - [x] 42.3 Add reduced motion option
    - Disable scanline/flicker effects
    - Disable animations
    - Respect prefers-reduced-motion
    - _Requirements: 22.1_
  
  - [ ]* 42.4 Verify WCAG 2.1 AA compliance
    - Test contrast ratios (both themes)
    - Test keyboard navigation
    - Test screen reader compatibility
    - Note: Manual testing required, cannot fully automate
    - _Requirements: 22.1_

- [ ] 43. Implement state synchronization
  - [x] 43.1 Add WebSocket for real-time updates
    - Connect to WebSocket on page load
    - Listen for WorkSpace state changes
    - Update UI within 10 seconds of changes
    - _Requirements: 22.2_
  
  - [ ]* 43.2 Write property test for state synchronization
    - **Property 74: State Synchronization Across Interfaces**
    - **Validates: Requirements 22.2**

- [x] 44. Checkpoint - Portal validation
  - Verify all pages render correctly in both themes
  - Verify WorkSpace provisioning works end-to-end
  - Verify Lucy chat integration works
  - Verify cost dashboard displays accurate data
  - Ensure all tests pass, ask the user if questions arise.


### Phase 8: Slack Integration

- [ ] 45. Implement Slack bot integration
  - [ ] 45.1 Set up Slack app
    - Create Slack app in workspace
    - Configure OAuth scopes
    - Set up event subscriptions
    - Configure slash commands
    - _Requirements: 5.2_
  
  - [ ] 45.2 Implement Slack bot backend
    - Handle Slack events (messages, mentions)
    - Route messages to Lucy service
    - Format Lucy responses for Slack
    - Handle interactive components (buttons, modals)
    - _Requirements: 5.2_
  
  - [ ] 45.3 Implement Slack notifications
    - Send budget warnings to Slack
    - Send WorkSpace status updates to Slack
    - Send stale workspace notifications to Slack
    - _Requirements: 12.2, 14.3_
  
  - [ ]* 45.4 Write integration tests for Slack bot
    - Test message handling
    - Test Lucy integration
    - Test notification delivery
    - _Requirements: 5.2_

- [ ] 46. Checkpoint - Slack integration validation
  - Verify Slack bot responds to messages
  - Verify Lucy integration works through Slack
  - Verify notifications are delivered
  - Ensure all tests pass, ask the user if questions arise.


### Phase 9: Observability and Monitoring

- [ ] 47. Implement metrics collection
  - [ ] 47.1 Add CloudWatch metrics
    - Emit WorkSpace provisioning time metrics
    - Emit WorkSpace provisioning success rate metrics
    - Emit Session connection latency metrics
    - Emit Session connection success rate metrics
    - Emit API response time metrics
    - _Requirements: 23.1_
  
  - [ ]* 47.2 Write property test for metrics emission
    - **Property 76: Metrics Emission**
    - **Validates: Requirements 23.1**
  
  - [ ] 47.3 Add Prometheus metrics
    - Expose /metrics endpoint
    - Add custom application metrics
    - Configure Prometheus scraping
    - _Requirements: 23.2_

- [ ] 48. Implement alerting
  - [ ] 48.1 Create CloudWatch alarms
    - Alert on provisioning time > 5 minutes
    - Alert on connection success rate < 95%
    - Alert on API error rate > 5%
    - Alert on database connection failures
    - _Requirements: 23.4, 23.5_
  
  - [ ]* 48.2 Write property test for slow provisioning alert
    - **Property 77: Slow Provisioning Alert**
    - **Validates: Requirements 23.4**
  
  - [ ]* 48.3 Write property test for connection degradation alert
    - **Property 78: Connection Degradation Alert**
    - **Validates: Requirements 23.5**
  
  - [ ] 48.4 Configure SNS notifications
    - Set up SNS topics for alerts
    - Configure email notifications
    - Configure Slack notifications
    - _Requirements: 23.4, 23.5_

- [ ] 49. Implement Grafana dashboards
  - [ ] 49.1 Create platform health dashboard
    - WorkSpace provisioning metrics
    - Session connection metrics
    - API performance metrics
    - Database performance metrics
    - _Requirements: 23.3_
  
  - [ ] 49.2 Create cost dashboard
    - Total spend over time
    - Spend by team, project, user
    - Budget utilization
    - Cost optimization opportunities
    - _Requirements: 11.2_
  
  - [ ] 49.3 Create Lucy performance dashboard
    - Lucy response time
    - Lucy tool execution success rate
    - Lucy conversation metrics
    - Lucy rate limiting metrics
    - _Requirements: 5.1_

- [ ] 50. Implement distributed tracing
  - [ ] 50.1 Set up OpenTelemetry
    - Configure OpenTelemetry SDK
    - Add tracing to all API endpoints
    - Add tracing to Lucy service
    - Add tracing to Cost Engine
    - _Requirements: 23.1_
  
  - [ ] 50.2 Configure trace export
    - Export traces to CloudWatch X-Ray
    - Configure sampling rules
    - Add custom span attributes
    - _Requirements: 23.1_

- [ ] 51. Implement structured logging
  - [ ] 51.1 Configure JSON logging
    - Set up structured logging for all services
    - Include request ID, user ID, action in all logs
    - Configure log levels (DEBUG, INFO, WARNING, ERROR)
    - _Requirements: 23.6_
  
  - [ ]* 51.2 Write property test for error logging
    - **Property 79: Error Logging with Context**
    - **Validates: Requirements 23.6**
  
  - [ ] 51.3 Configure log aggregation
    - Send all logs to CloudWatch Logs
    - Configure log retention (90 days for most logs)
    - Set up log insights queries
    - _Requirements: 23.6_

- [ ] 52. Checkpoint - Observability validation
  - Verify all metrics are being collected
  - Verify alerts trigger correctly
  - Verify Grafana dashboards display data
  - Verify distributed tracing works end-to-end
  - Ensure all tests pass, ask the user if questions arise.


### Phase 10: Security Hardening

- [ ] 53. Implement network security
  - [ ] 53.1 Configure network policies
    - Create Kubernetes network policies for pod-to-pod communication
    - Restrict WorkSpaces VPC to no direct internet access
    - Configure NAT gateway with egress allowlist
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ]* 53.2 Write property test for network isolation
    - **Property 32: Isolated VPC Placement**
    - **Property 33: No Direct Internet Access**
    - **Property 34: Controlled Egress Routing**
    - **Property 35: Egress Traffic Logging**
    - **Property 36: Ingress Traffic Filtering**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
  
  - [ ] 53.2 Configure VPC endpoints
    - Create VPC endpoints for S3, Secrets Manager, FSx
    - Configure security groups for VPC endpoints
    - _Requirements: 9.2_

- [ ] 54. Implement data exfiltration prevention
  - [ ] 54.1 Configure WorkSpaces Group Policies
    - Disable clipboard operations via Group Policy
    - Disable USB device redirection via Group Policy
    - Disable drive redirection via Group Policy
    - Disable file transfer via Group Policy
    - Disable printing via Group Policy
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 54.2 Verify data exfiltration prevention (manual testing required)
    - Test clipboard disabled (attempt copy/paste)
    - Test USB disabled (attempt device connection)
    - Test drive mapping disabled (attempt file transfer)
    - Test printing disabled (attempt print)
    - Note: These are manual security tests
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 55. Implement secrets security
  - [ ] 55.1 Configure secrets rotation
    - Set up automatic rotation for database credentials (30 days)
    - Set up automatic rotation for API keys (90 days)
    - Configure rotation Lambda functions
    - _Requirements: 21.4_
  
  - [ ] 55.2 Implement secrets scrubbing
    - Add log scrubbing to prevent secrets in logs
    - Add pre-commit hooks to prevent secrets in code
    - Configure secret scanning in CI/CD
    - _Requirements: 21.1_
  
  - [ ]* 55.3 Verify no secrets in code or logs
    - Run secret scanning tools
    - Verify log scrubbing works
    - Test pre-commit hooks
    - _Requirements: 21.1_

- [ ] 56. Implement encryption
  - [ ] 56.1 Configure encryption at rest
    - Enable RDS encryption (AES-256)
    - Enable FSx ONTAP encryption (AES-256)
    - Enable S3 encryption (SSE-S3)
    - Enable WorkSpaces volume encryption (KMS)
    - _Requirements: 9.1_
  
  - [ ] 56.2 Configure encryption in transit
    - Enforce TLS 1.3 for all API traffic
    - Configure WSP encryption for WorkSpaces sessions
    - _Requirements: 3.1_

- [ ] 57. Implement security scanning
  - [ ] 57.1 Set up SAST scanning
    - Configure SAST tool (e.g., Semgrep, SonarQube)
    - Add SAST to CI/CD pipeline
    - Require SAST pass for PR merge
    - _Requirements: 25.4_
  
  - [ ] 57.2 Set up DAST scanning
    - Configure DAST tool (e.g., OWASP ZAP)
    - Run DAST scans before deployment
    - Require DAST pass for deployment
    - _Requirements: 25.4_
  
  - [ ] 57.3 Set up dependency scanning
    - Configure dependency scanning (e.g., Dependabot, Snyk)
    - Scan for vulnerable dependencies
    - Auto-update dependencies when possible
    - _Requirements: 25.4_

- [ ] 58. Implement IAM least privilege
  - [ ] 58.1 Configure service IAM roles
    - Create least-privilege role for WorkSpaces service
    - Create least-privilege role for Provisioning service
    - Create least-privilege role for Cost Engine
    - Create read-only role for monitoring
    - _Requirements: 8.3, 8.4_
  
  - [ ]* 58.2 Verify IAM roles are least-privilege
    - Test that services cannot access unauthorized resources
    - Verify role permissions are minimal
    - _Requirements: 8.3, 8.4_

- [ ] 59. Checkpoint - Security validation
  - Verify network isolation is enforced
  - Verify data exfiltration prevention works
  - Verify secrets are rotated and not exposed
  - Verify encryption is enabled everywhere
  - Verify security scans pass
  - Ensure all tests pass, ask the user if questions arise.


### Phase 11: High Availability and Reliability

- [ ] 60. Implement high availability
  - [ ] 60.1 Configure multi-AZ deployment
    - Deploy RDS in Multi-AZ mode
    - Deploy FSx ONTAP in Multi-AZ mode
    - Deploy EKS nodes across 3 availability zones
    - _Requirements: 24.1, 24.3_
  
  - [ ] 60.2 Configure auto-scaling
    - Set up HPA for API pods (target 70% CPU)
    - Set up HPA for Lucy service pods (based on queue depth)
    - Set up HPA for Cost Engine pods (based on backlog)
    - Set up HPA for Celery workers (based on queue length)
    - _Requirements: 24.1_
  
  - [ ] 60.3 Configure health checks
    - Implement /health endpoint for all services
    - Implement /ready endpoint for all services
    - Configure Kubernetes liveness probes (30-second interval)
    - Configure Kubernetes readiness probes
    - _Requirements: 24.4_
  
  - [ ]* 60.4 Write property test for component auto-recovery
    - **Property 80: Component Auto-Recovery**
    - **Validates: Requirements 24.5**

- [ ] 61. Implement fault tolerance
  - [ ] 61.1 Add circuit breaker pattern
    - Implement circuit breaker for AWS APIs
    - Implement circuit breaker for Okta
    - Implement circuit breaker for Secrets Manager
    - Configure thresholds (5 failures, 30-second timeout)
    - _Requirements: 24.3_
  
  - [ ] 61.2 Add retry logic
    - Implement exponential backoff for transient failures
    - Retry AWS API errors (1s, 2s, 4s, 8s, 16s max)
    - Retry capacity errors in alternative regions
    - _Requirements: 1.1_
  
  - [ ] 61.3 Implement graceful degradation
    - Allow provisioning if Cost_Engine unavailable (log warning)
    - Return error if Lucy unavailable (direct to Portal/CLI)
    - Fall back to on-demand if pre-warmed pool empty
    - _Requirements: 19.2_

- [ ] 62. Implement backup and recovery
  - [ ] 62.1 Configure automated backups
    - Enable RDS automated backups (daily, 30-day retention)
    - Enable FSx ONTAP automated backups (daily, 30-day retention)
    - Enable S3 versioning for blueprints
    - _Requirements: 10.3_
  
  - [ ] 62.2 Implement point-in-time recovery
    - Configure RDS PITR
    - Document recovery procedures
    - Test recovery process
    - _Requirements: 10.3_
  
  - [ ] 62.3 Create disaster recovery runbooks
    - Document RTO/RPO targets
    - Create runbooks for common failure scenarios
    - Test disaster recovery procedures
    - _Requirements: 24.3_

- [ ] 63. Implement change management
  - [ ] 63.1 Set up blue/green deployments
    - Configure blue/green deployment for API services
    - Configure blue/green deployment for Lucy service
    - Configure blue/green deployment for Cost Engine
    - _Requirements: 25.4_
  
  - [ ] 63.2 Set up canary deployments
    - Configure canary deployment for high-risk changes
    - Set up traffic splitting (10% canary, 90% stable)
    - Configure automatic rollback on errors
    - _Requirements: 25.4_
  
  - [ ] 63.3 Implement automated rollback
    - Configure rollback triggers (error rate > 5%)
    - Implement automatic rollback on deployment failures
    - _Requirements: 25.4_

- [ ] 64. Checkpoint - High availability validation
  - Verify services survive AZ failures
  - Verify auto-scaling works correctly
  - Verify health checks detect failures
  - Verify circuit breakers prevent cascading failures
  - Verify backups are created successfully
  - Ensure all tests pass, ask the user if questions arise.


### Phase 12: IDE Integration

- [ ] 65. Implement VS Code Remote integration
  - [ ] 65.1 Configure VS Code Remote SSH
    - Set up SSH access to WorkSpaces
    - Configure SSH keys and authentication
    - Integrate with SSO credentials
    - _Requirements: 18.1, 18.4_
  
  - [ ] 65.2 Maintain connection state
    - Persist VS Code connection state across stop/start
    - Restore workspace state on reconnection
    - _Requirements: 18.5_
  
  - [ ]* 65.3 Write property test for IDE authentication
    - **Property 61: IDE SSO Authentication**
    - **Validates: Requirements 18.4**
  
  - [ ]* 65.4 Write property test for IDE connection persistence
    - **Property 62: IDE Connection Persistence**
    - **Validates: Requirements 18.5**

- [ ] 66. Implement JetBrains IDE integration
  - [ ] 66.1 Configure JetBrains Gateway
    - Set up JetBrains Gateway for remote connection
    - Configure authentication with SSO
    - _Requirements: 18.2, 18.4_
  
  - [ ] 66.2 Maintain connection state
    - Persist JetBrains connection state across stop/start
    - Restore project state on reconnection
    - _Requirements: 18.5_

- [ ] 67. Implement browser-based IDE
  - [ ] 67.1 Set up code-server or similar
    - Deploy browser-based IDE on WorkSpaces
    - Configure authentication with SSO
    - _Requirements: 18.3, 18.4_
  
  - [ ]* 67.2 Write integration tests for IDE access
    - Test VS Code Remote connection
    - Test JetBrains Gateway connection
    - Test browser-based IDE access
    - _Requirements: 18.1, 18.2, 18.3_

- [ ] 68. Checkpoint - IDE integration validation
  - Verify VS Code Remote connects successfully
  - Verify JetBrains Gateway connects successfully
  - Verify browser-based IDE is accessible
  - Verify connection state persists across stop/start
  - Ensure all tests pass, ask the user if questions arise.


### Phase 13: Multi-Interface Consistency

- [ ] 69. Implement feature parity validation
  - [ ] 69.1 Create feature parity test suite
    - Test WorkSpace provisioning via Portal, CLI, Lucy
    - Test WorkSpace start/stop via Portal, CLI, Lucy
    - Test cost queries via Portal, CLI, Lucy
    - _Requirements: 22.1_
  
  - [ ]* 69.2 Write property test for feature parity
    - **Property 73: Feature Parity Across Interfaces**
    - **Validates: Requirements 22.1**

- [ ] 70. Implement state synchronization
  - [ ] 70.1 Add WebSocket for real-time updates
    - Implement WebSocket server
    - Broadcast state changes to all connected clients
    - Update Portal UI within 10 seconds
    - _Requirements: 22.2_
  
  - [ ]* 70.2 Write property test for state synchronization
    - **Property 74: State Synchronization Across Interfaces**
    - **Validates: Requirements 22.2**

- [ ] 71. Implement consistent error messages
  - [ ] 71.1 Create error message catalog
    - Define error codes and messages
    - Ensure identical messages across Portal, CLI, Lucy
    - _Requirements: 22.5_
  
  - [ ]* 71.2 Write property test for error message consistency
    - **Property 75: Error Message Consistency**
    - **Validates: Requirements 22.5**

- [ ] 72. Checkpoint - Multi-interface consistency validation
  - Verify all features work identically across interfaces
  - Verify state changes sync within 10 seconds
  - Verify error messages are consistent
  - Ensure all tests pass, ask the user if questions arise.


### Phase 14: End-to-End Integration Testing

- [ ] 73. Implement end-to-end test scenarios
  - [ ] 73.1 Test complete provisioning flow
    - Engineer provisions WorkSpace via Portal
    - WorkSpace reaches AVAILABLE state within 5 minutes
    - Engineer connects via WSP
    - Verify watermark is displayed
    - Engineer disconnects
    - WorkSpace auto-stops after idle timeout
    - _Requirements: 1.1, 1.7, 3.1, 7.6_
  
  - [ ] 73.2 Test Lucy provisioning flow
    - Engineer asks Lucy "I need a GPU workspace"
    - Lucy recommends bundle and shows cost estimate
    - Engineer confirms
    - Lucy provisions WorkSpace
    - Engineer connects and runs simulation
    - _Requirements: 5.3, 5.4_
  
  - [ ] 73.3 Test Blueprint workflow
    - Team lead creates Blueprint
    - Engineer provisions WorkSpace from Blueprint
    - Verify software is installed correctly
    - _Requirements: 2.1, 2.2, 1.6_
  
  - [ ] 73.4 Test budget enforcement flow
    - Engineer exceeds 80% budget
    - Receives warning notification
    - Engineer attempts provisioning at 100% budget
    - Provisioning is blocked across all interfaces
    - _Requirements: 12.2, 12.3, 12.4, 12.5, 12.6_
  
  - [ ] 73.5 Test contractor workflow
    - Contractor with time-bound credentials logs in
    - Contractor provisions restricted bundle
    - Credentials expire
    - Access is denied
    - _Requirements: 8.5, 8.6_

- [ ] 74. Implement performance testing
  - [ ] 74.1 Test provisioning under load
    - Simulate 100 concurrent provisioning requests
    - Verify all complete within 5 minutes
    - Verify no errors or timeouts
    - _Requirements: 1.1_
  
  - [ ] 74.2 Test Lucy response time
    - Measure Lucy response time (p50, p95, p99)
    - Verify p95 < 2 seconds
    - _Requirements: 5.1_
  
  - [ ] 74.3 Test cost dashboard performance
    - Load cost dashboard with 1000+ workspaces
    - Verify query time < 5 seconds
    - _Requirements: 11.3_
  
  - [ ] 74.4 Test WSP streaming latency
    - Measure WSP connection latency
    - Verify latency < 30ms under normal conditions
    - _Requirements: 3.5_

- [ ] 75. Checkpoint - End-to-end validation
  - Verify all end-to-end scenarios pass
  - Verify performance meets requirements
  - Verify system handles load correctly
  - Ensure all tests pass, ask the user if questions arise.


### Phase 15: Documentation and Deployment

- [ ] 76. Create documentation
  - [ ] 76.1 Write API documentation
    - Document all API endpoints with OpenAPI
    - Add request/response examples
    - Document error codes and messages
    - _Requirements: 22.1_
  
  - [ ] 76.2 Write user documentation
    - Create user guide for Portal
    - Create user guide for CLI
    - Create user guide for Lucy
    - Document common workflows
    - _Requirements: 22.1_
  
  - [ ] 76.3 Write operator documentation
    - Document deployment procedures
    - Document monitoring and alerting
    - Document troubleshooting procedures
    - Document disaster recovery procedures
    - _Requirements: 23.3, 24.3_
  
  - [ ] 76.4 Write architecture documentation
    - Document system architecture
    - Document data models
    - Document security controls
    - Document AWS Well-Architected alignment
    - _Requirements: 25.1_

- [ ] 77. Set up CI/CD pipeline
  - [ ] 77.1 Configure GitHub Actions
    - Set up automated testing on PR
    - Set up SAST/DAST scanning
    - Set up dependency scanning
    - Require all checks to pass before merge
    - _Requirements: 25.4_
  
  - [ ] 77.2 Configure deployment pipeline
    - Set up automated deployment to dev
    - Set up manual approval for staging
    - Set up manual approval for production
    - Configure blue/green deployment
    - _Requirements: 25.4_
  
  - [ ] 77.3 Configure infrastructure deployment
    - Set up Terraform plan on PR
    - Require infrastructure team review
    - Set up automated apply after approval
    - _Requirements: 25.4_

- [ ] 78. Deploy to staging environment
  - [ ] 78.1 Deploy infrastructure to staging
    - Apply Terraform modules
    - Deploy EKS cluster
    - Deploy RDS and FSx
    - Configure WorkSpaces directory
    - _Requirements: 25.5_
  
  - [ ] 78.2 Deploy applications to staging
    - Deploy API services
    - Deploy Lucy service
    - Deploy Cost Engine
    - Deploy Portal
    - _Requirements: 25.5_
  
  - [ ] 78.3 Run smoke tests in staging
    - Test basic provisioning flow
    - Test Lucy integration
    - Test cost tracking
    - Verify monitoring and alerting
    - _Requirements: 25.5_

- [ ] 79. Deploy to production environment
  - [ ] 79.1 Deploy infrastructure to production
    - Apply Terraform modules
    - Deploy EKS cluster
    - Deploy RDS and FSx
    - Configure WorkSpaces directory
    - _Requirements: 25.5_
  
  - [ ] 79.2 Deploy applications to production
    - Deploy API services with blue/green
    - Deploy Lucy service with blue/green
    - Deploy Cost Engine with blue/green
    - Deploy Portal
    - _Requirements: 25.5_
  
  - [ ] 79.3 Run smoke tests in production
    - Test basic provisioning flow
    - Test Lucy integration
    - Test cost tracking
    - Verify monitoring and alerting
    - _Requirements: 25.5_
  
  - [ ] 79.4 Monitor for 24 hours
    - Monitor error rates
    - Monitor performance metrics
    - Monitor cost metrics
    - Verify no critical issues
    - _Requirements: 23.1, 24.2_

- [ ] 80. Final checkpoint - Production validation
  - Verify all services are healthy in production
  - Verify monitoring and alerting work correctly
  - Verify end-to-end flows work in production
  - Verify documentation is complete and accurate
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test-related sub-tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- All code must pass type checking (mypy for Python, TypeScript strict mode)
- All PRs must pass SAST/DAST security scans before merge
- Infrastructure changes require Terraform plan review before apply
- Lucy prompt changes require evaluation test pass (>95% success rate) before deployment

## Testing Configuration

**Property-Based Testing**:
- Framework: `hypothesis` for Python, `fast-check` for TypeScript
- Minimum 100 iterations per property test
- Tag format: `# Feature: robco-forge, Property {number}: {property_text}`

**Code Coverage Requirements**:
- Backend (Python): 80% minimum, 100% for security-critical paths
- Frontend (TypeScript): 70% minimum, 100% for budget enforcement
- CLI (TypeScript): 80% minimum

**Security Testing**:
- SAST scans required on every PR
- DAST scans required before deployment
- Dependency scanning with auto-updates
- Manual penetration testing for RBAC bypass attempts

## Deployment Strategy

**Environments**:
- Development: Automated deployment on merge to main
- Staging: Manual approval required
- Production: Manual approval + 24-hour monitoring

**Deployment Method**:
- Blue/green deployment for zero-downtime updates
- Canary deployment for high-risk changes
- Automated rollback on error rate > 5%

## Success Criteria

The RobCo Forge platform is considered complete when:
1. All 80 tasks are completed (excluding optional test sub-tasks)
2. All property tests pass (81 properties validated)
3. Code coverage meets minimum thresholds
4. All security scans pass
5. End-to-end scenarios work in production
6. Monitoring and alerting are operational
7. Documentation is complete
8. Platform achieves 99.9% uptime SLA


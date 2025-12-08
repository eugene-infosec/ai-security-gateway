# System Architecture & Trust Boundaries

## High-Level Data Flow

graph LR
    User[Client / User] -->|JWT| Edge[Edge Auth (Cognito/Gateway)]
    Edge -->|Verified Claims| App[Security Gateway (Lambda)]
    
    subgraph "Trusted Compute (The Invariant Boundary)"
        App -->|1. Derive Auth| Policy[Policy Engine]
        App -->|2. Scoped Query| Store[Data Store (DynamoDB)]
        App -->|3. Audit Event| Logs[Safe Logger]
    end
# Privacy and Data Handling

## Overview

ResilAI is designed with privacy-by-design principles. This page describes data categories, usage boundaries, and retention behavior.

## Data Categories

### Identity Data

| Data | Purpose | Storage |
| --- | --- | --- |
| Email | Authentication and account identification | Firebase Auth |
| Display name | UX personalization | Firebase Auth |
| User ID | Access and ownership checks | Application database |

### Organization and Assessment Data

| Data | Purpose | Storage |
| --- | --- | --- |
| Organization metadata | Reporting context | Database |
| Assessment answers | Scoring input | Database |
| Scores and findings | Risk analysis outputs | Database |
| Timestamps | Auditability and operations | Database |

### Report Data

| Data | Purpose | Storage |
| --- | --- | --- |
| PDF artifacts | Download and sharing | Object storage / report store |
| Report metadata | Retrieval and filtering | Database |

## Retention and Deletion

- User and organization data persists until deletion actions are taken
- Application and audit logs are retained for operational/security needs
- Data deletion operations are available via API routes

## Public Beta Synthetic Data

Public beta environments may include synthetic sample data for product demonstration and validation.

## Access Model

- Data access is scoped to authenticated ownership context
- Platform operators do not sell customer data
- Third-party sharing is limited to required infrastructure providers

## AI Processing Notes

When narrative features are enabled:

- Prompts are generated from assessment context
- Scoring remains deterministic and non-LLM
- LLM use can be disabled by environment policy

## Contact

For privacy inquiries: `purvansh95b@gmail.com`

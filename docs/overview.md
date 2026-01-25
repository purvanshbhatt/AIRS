# AIRS Overview

## What is AIRS?

**AIRS (AI Incident Readiness Score)** is a comprehensive security readiness assessment platform designed for organizations preparing for AI-driven threats and incidents. It provides a structured, quantitative approach to measuring and improving your organization's security posture.

## Who is AIRS For?

| Audience | Use Case |
|----------|----------|
| **CISOs & Security Leaders** | Board-ready reports, maturity benchmarking, remediation roadmaps |
| **Security Teams** | Gap analysis, prioritized findings, framework compliance tracking |
| **Consultants & Auditors** | Standardized assessments, client deliverables, repeatable methodology |
| **Academic Researchers** | Security posture studies, quantitative security metrics research |

## Key Capabilities

### 1. Structured Assessment
- 25 questions across 5 security domains
- Deterministic scoring (0-100 scale)
- Industry-standard maturity levels (1-4)

### 2. Framework Mapping
- **MITRE ATT&CK** technique coverage analysis
- **CIS Controls v8** compliance tracking (IG1/IG2/IG3)
- **OWASP Top 10** risk correlation

### 3. Executive Reporting
- Professional PDF reports with branding
- 30/60/90 day remediation roadmaps
- Baseline comparisons (SMB, Enterprise, Healthcare, Financial)

### 4. AI-Enhanced Narratives
- LLM-generated executive summaries (optional)
- AI never modifies scores or findings
- Full transparency on AI vs. deterministic content

## Demo Flow

1. **Create Organization** → Set up your company profile
2. **Start Assessment** → Answer 25 security questions
3. **View Results** → See scores, findings, and framework mappings
4. **Generate Report** → Download professional PDF or save to library
5. **Track Progress** → Compare assessments over time

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React SPA     │────▶│   FastAPI       │────▶│   Cloud SQL     │
│   (Frontend)    │     │   (Backend)     │     │   (PostgreSQL)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       
        ▼                       ▼                       
┌─────────────────┐     ┌─────────────────┐     
│   Firebase      │     │   Cloud Storage │     
│   (Auth)        │     │   (Reports)     │     
└─────────────────┘     └─────────────────┘     
```

## What Makes AIRS Different

| Feature | AIRS | Traditional Tools |
|---------|------|-------------------|
| **Scoring** | Deterministic, reproducible | Often subjective |
| **AI Transparency** | AI for narrative only, clearly labeled | Black-box AI scoring |
| **Framework Mapping** | Automatic MITRE/CIS/OWASP | Manual mapping required |
| **Deployment** | Cloud-native, multi-tenant | On-premises heavy |
| **Time to Value** | 15-minute assessment | Days/weeks |

## Getting Started

Visit the [Live Demo](https://airs-api-<project-id>.run.app) to try AIRS with sample data.

For technical documentation, see:
- [Methodology](methodology.md) - Scoring domains and formulas
- [Frameworks](frameworks.md) - MITRE/CIS/OWASP mapping
- [Security](security.md) - Authentication and data protection
- [Privacy](privacy.md) - Data handling and retention

# Architecture Overview

ResilAI is built with a split architecture that keeps scoring deterministic and AI-assisted explanation isolated.

## High-Level Flow

1. Frontend collects assessment input and displays outputs
2. FastAPI backend validates and processes assessment data
3. Deterministic scoring engine computes readiness score and gap details
4. Gemini-based narrative layer generates executive interpretation
5. Reports are rendered for security and leadership audiences

## Components

- Frontend: React + Vite
- Backend: FastAPI
- Scoring: deterministic rubric-driven service
- AI Narrative: Gemini Flash for qualitative summary
- Hosting: Google Cloud Run with managed cloud services

## Trust Boundary Design

- Scoring decisions are rule-based and auditable
- AI output does not modify readiness score computation
- Demo environment is configured read-only to protect presentation data integrity

## Deployment Automation

Cloud deployment scripts automate build and release flow for repeatable environment updates.

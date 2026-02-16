# ResilAI - AI Incident Readiness Score

<p align="center">
  <img src="frontend/public/airs-logo-dark.png" alt="ResilAI Logo" width="200"/>
</p>

<p align="center">
  <strong>Quantify your organization's security readiness. Get actionable insights in 15 minutes.</strong>
</p>

<p align="center">
  <a href="https://airs-staging-0384513977.web.app">🚀 Public Beta</a> •
  <a href="#features">Features</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#security">Security</a>
</p>

---

## 🎯 What is ResilAI?

**ResilAI (AI Incident Readiness Score)** is a modern security assessment platform that helps organizations measure and improve their incident readiness posture. Complete a 15-minute assessment and receive:

- 📊 **Quantitative Score** (0-100) with maturity level (1-4)
- 🔍 **Prioritized Findings** with remediation recommendations  
- 🗺️ **30/60/90 Day Roadmap** for security improvements
- 📋 **Framework Mapping** to MITRE ATT&CK, CIS Controls, OWASP
- 📄 **Executive PDF Report** ready for board presentation

## 🚀 Public Beta

| Resource | Link |
|----------|------|
| **Web Application (Public Beta)** | [airs-staging-0384513977.web.app](https://airs-staging-0384513977.web.app) |
| **API Health** | [/health](https://airs-api-staging-0384513977-knu3wsxymq-uc.a.run.app/health) |
| **LLM Status** | [/health/llm](https://airs-api-staging-0384513977-knu3wsxymq-uc.a.run.app/health/llm) |
| **Backend API Docs** | [/docs](https://airs-api-staging-0384513977-knu3wsxymq-uc.a.run.app/docs) |

### Quick Demo Walkthrough

1. **Sign In** → Use Google OAuth or create an account
2. **Create Organization** → Add a company name (use "Demo Corp")
3. **Start Assessment** → Answer 25 security questions (~10 min)
4. **View Results** → Explore scores, findings, and framework mappings
5. **Generate Report** → Download a professional PDF report

---

## ✨ Features

### Security Assessment
- **25 Questions** across 5 security domains
- **Deterministic Scoring** — reproducible results, no black-box AI
- **Baseline Comparison** — compare against SMB, Enterprise, Healthcare, Financial benchmarks

### Findings & Roadmap
- **Automated Gap Analysis** — findings generated from scoring gaps
- **Severity Classification** — Critical, High, Medium, Low prioritization
- **Remediation Roadmap** — 30/60/90 day action plan

### Framework Integration

| Framework | What You Get |
|-----------|-------------|
| **MITRE ATT&CK** | Technique coverage analysis |
| **CIS Controls v8** | IG1/IG2/IG3 compliance tracking |
| **OWASP Top 10** | Web application risk mapping |

### Reporting
- **Professional PDF Reports** — branded, board-ready
- **Report Library** — save and manage historical reports
- **Snapshot Preservation** — reports locked at generation time

### AI Transparency 🤖

ResilAI uses AI (Google Gemini) for narrative generation **only**:

| ✅ AI Generates | ❌ AI Does NOT Modify |
|----------------|----------------------|
| Executive summaries | Assessment scores |
| Roadmap narratives | Finding severity |
| Business-friendly insights | Recommendations |

> All scores, findings, and framework mappings are computed deterministically. AI enhances readability, not results.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React SPA     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   TypeScript    │     │   Python 3.11   │     │   Cloud SQL     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       
        ▼                       ▼                       
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Firebase      │     │   Cloud Storage │     │   Gemini API    │
│   Auth + Host   │     │   (Reports)     │     │   (Narratives)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Tech Stack:**
- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite
- **Backend:** FastAPI, Python 3.11, SQLAlchemy
- **Database:** PostgreSQL (Cloud SQL)
- **Auth:** Firebase Authentication
- **Hosting:** Firebase Hosting (frontend), Cloud Run (API)
- **AI:** Google Gemini 3 Flash (`gemini-3-flash-preview`, narratives only)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Overview](docs/overview.md) | What ResilAI is, who it's for |
| [Methodology](docs/methodology.md) | Scoring domains, formulas, maturity levels |
| [Frameworks](docs/frameworks.md) | MITRE/CIS/OWASP mapping philosophy |
| [Security](docs/security.md) | Auth, tenancy, encryption, logging |
| [Privacy](docs/privacy.md) | Data handling, retention, deletion |

---

## 🔒 Security

ResilAI is built with enterprise security requirements in mind:

| Control | Implementation |
|---------|----------------|
| **Authentication** | Firebase Auth (JWT validation) |
| **Multi-Tenancy** | Row-level isolation by user ID |
| **Data Encryption** | AES-256 at rest, TLS 1.2+ in transit |
| **Secrets** | Google Secret Manager |
| **Logging** | Structured logs with request correlation |
| **Signed URLs** | Time-limited report access (15 min) |

📖 See [docs/security.md](docs/security.md) for full details.

---

## 🏃 Run Frontend Locally

```bash
# Clone the repository
git clone https://github.com/purvanshbhatt/AIRS.git
cd AIRS/frontend

# Install dependencies
npm install

# Configure environment (uses hosted API)
cp .env.example .env

# Start development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📦 Project Structure

```
ResilAI/
├── frontend/               # React TypeScript SPA
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Route pages
│   │   ├── contexts/       # React contexts
│   │   └── services/       # API services
│   └── public/             # Static assets (logos)
├── docs/                   # Documentation
│   ├── overview.md
│   ├── methodology.md
│   ├── frameworks.md
│   ├── security.md
│   └── privacy.md
├── openapi/                # API specification
└── sample_reports/         # Example PDF outputs
```

---

## 🤝 Contact

- **Demo Questions:** Schedule a walkthrough
- **Enterprise Licensing:** Contact for pricing
- **Security Issues:** security@[domain]

---

## 📄 License

This showcase repository is provided for demonstration purposes.

---

<p align="center">
  <img src="frontend/public/favicon.png" alt="ResilAI Icon" width="40"/>
</p>

<p align="center">
  Built with ❤️ for security teams everywhere
</p>


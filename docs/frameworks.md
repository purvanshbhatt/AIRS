# Framework Mapping

## Overview

ResilAI automatically maps assessment findings to industry-standard security frameworks, enabling organizations to understand their compliance posture without manual cross-referencing.

## Supported Frameworks

### MITRE ATT&CK

**Purpose:** Understand which attack techniques your controls address

| Metric | Description |
|--------|-------------|
| Techniques Referenced | ATT&CK techniques covered by your controls |
| Coverage Percentage | % of relevant techniques with mitigation |
| Tactic Distribution | Breakdown by ATT&CK tactic (Initial Access, Execution, etc.) |

**How It Works:**
- Each assessment question is mapped to relevant ATT&CK techniques
- Positive answers indicate technique coverage
- Gaps reveal attack surface exposure

**Example Mapping:**
```
Question: "Do you have email security filtering?"
Maps to: T1566 (Phishing), T1566.001 (Spearphishing Attachment)
```

### CIS Controls v8

**Purpose:** Track compliance with CIS Critical Security Controls

| Implementation Group | Target Audience |
|---------------------|-----------------|
| **IG1** | Small organizations, essential hygiene |
| **IG2** | Mid-size, sector-specific risks |
| **IG3** | Large/regulated, advanced threats |

**Metrics Provided:**
- Controls referenced count
- IG1/IG2/IG3 coverage percentages
- Gap analysis by control family

**Example Mapping:**
```
Question: "What is your log retention period?"
Maps to: CIS 8.1 (Establish and Maintain Audit Log Management)
```

### OWASP Top 10

**Purpose:** Web application security risk awareness

ResilAI maps relevant findings to OWASP Top 10 2021:

| ID | Risk Category |
|----|---------------|
| A01 | Broken Access Control |
| A02 | Cryptographic Failures |
| A03 | Injection |
| A05 | Security Misconfiguration |
| A07 | Identification and Authentication Failures |
| A09 | Security Logging and Monitoring Failures |

## Mapping Philosophy

### Conservative Approach
ResilAI uses a **conservative mapping** strategy:
- Only maps when there's a clear, defensible relationship
- Avoids over-claiming coverage
- Focuses on controls that demonstrably mitigate techniques

### Question-Level Mapping
Mappings are defined at the question level in the rubric:
```json
{
  "id": "dc_01",
  "text": "EDR deployed on all endpoints?",
  "mitre": ["T1059", "T1053", "T1547"],
  "cis": ["CIS-10.1", "CIS-10.2"],
  "owasp": []
}
```

### Finding-Level Aggregation
When generating findings, ResilAI aggregates:
- All framework references for the source question
- Impact assessment based on technique severity
- Remediation guidance aligned with framework controls

## Coverage Calculations

### MITRE Coverage
```
Coverage % = (Techniques with positive answers / Total mapped techniques) Ã— 100
```

### CIS Coverage
```
IG Coverage % = (Controls met / Total controls in IG) Ã— 100
```

### OWASP Relevance
```
Relevant findings mapped to OWASP categories (count-based)
```

## Report Integration

Framework mappings appear in:

1. **Results Dashboard** â†’ Framework tab with visual coverage charts
2. **PDF Reports** â†’ Dedicated framework mapping section
3. **API Response** â†’ `framework_mapping` object with full details

## Limitations

| What We Do | What We Don't Do |
|------------|------------------|
| Map to relevant techniques | Claim full framework compliance |
| Show coverage gaps | Replace formal audits |
| Guide prioritization | Guarantee regulatory compliance |
| Provide starting point | Substitute for penetration testing |

## Keeping Mappings Current

- Framework mappings are version-controlled in the rubric
- Updates follow framework version releases (e.g., CIS v8.1)
- Breaking changes are documented in release notes

# Framework Mapping

## Overview

ResilAI maps assessment outputs to major security frameworks so teams can move from readiness scoring to recognized control language.

## Supported Frameworks

### MITRE ATT&CK

Used to connect control gaps to adversary techniques.

- Technique reference counts
- Tactic-level visibility
- Coverage-oriented insights

### CIS Controls v8

Used for control maturity and implementation planning.

- Control mapping by finding
- Implementation group context (IG1, IG2, IG3)
- Coverage gap identification

### OWASP

Used for application and AI-adjacent risk framing.

- Category-aligned findings
- Risk communication in familiar security taxonomy

## Mapping Approach

ResilAI uses conservative mapping:

- Mappings are applied only where relationship is defensible
- Coverage signals are directional, not certification claims
- Mapping metadata is included with findings and report outputs

## Example Structure

```json
{
  "finding_id": "abc123",
  "title": "Insufficient log retention",
  "mitre_refs": [{ "id": "T1070", "name": "Indicator Removal" }],
  "cis_refs": [{ "id": "CIS 8.1", "name": "Audit Log Management" }],
  "owasp_refs": [{ "id": "A09", "name": "Security Logging and Monitoring Failures" }]
}
```

## Coverage Calculations

- MITRE coverage percentage: techniques positively covered / total mapped techniques
- CIS coverage percentage: controls met / total mapped controls
- OWASP snapshot: count of mapped findings by category

## Where Mapping Appears

- Results framework views
- Executive and detailed PDF exports
- API payloads (`framework_mapping` and export endpoints)

## Limitations

Framework mapping in ResilAI supports prioritization and communication. It does not replace formal audits, penetration testing, or regulatory attestation.

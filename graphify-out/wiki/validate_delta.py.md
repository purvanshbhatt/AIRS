# validate_delta.py

> 22 nodes · cohesion 0.12

## Key Concepts

- **validate_delta.py** (15 connections) — `scripts/validate_delta.py`
- **CVEEnrichmentService** (12 connections) — `app/services/cve/cve_enrichment.py`
- **cve_enrichment.py** (8 connections) — `app/services/cve/cve_enrichment.py`
- **AWSConfigPoller** (7 connections) — `app/services/discovery/aws_ssm_poller.py`
- **main()** (7 connections) — `scripts/validate_delta.py`
- **EnrichmentResult** (5 connections) — `app/services/cve/cve_enrichment.py`
- **.bulk_enrich()** (4 connections) — `app/services/cve/cve_enrichment.py`
- **.enrich_software()** (4 connections) — `app/services/cve/cve_enrichment.py`
- **.__init__()** (3 connections) — `app/services/cve/cve_enrichment.py`
- **VulnerabilitySignal** (3 connections) — `app/services/cve/cve_enrichment.py`
- **.__init__()** (3 connections) — `app/services/technology_intelligence.py`
- **.compute_evidence_hash()** (2 connections) — `app/services/cve/cve_enrichment.py`
- **Session** (1 connections)
- **AIRS CVE Enrichment Engine. Maps normalized software and versions to known…** (1 connections) — `app/services/cve/cve_enrichment.py`
- **Enrich a batch of normalized software records. Args: inventory_items: List of…** (1 connections) — `app/services/cve/cve_enrichment.py`
- **A single vulnerability mapped to a software product.** (1 connections) — `app/services/cve/cve_enrichment.py`
- **The result of enriching a specific software product/version.** (1 connections) — `app/services/cve/cve_enrichment.py`
- **Compute SHA-256 hash of the enrichment result for the evidence log.** (1 connections) — `app/services/cve/cve_enrichment.py`
- **Enriches software inventory with CVE data. NOTE: In Sprint 1, we DO NOT create…** (1 connections) — `app/services/cve/cve_enrichment.py`
- **Enrich a single software product with CVE data. In production, this would query…** (1 connections) — `app/services/cve/cve_enrichment.py`
- **Poller for AWS Systems Manager Inventory (SSM). Demonstrates real staging…** (1 connections) — `app/services/discovery/aws_ssm_poller.py`
- **Session** (1 connections)

## Relationships

- [test_reliability.py](test_reliability.py.md) (10 shared connections)
- [SoftwareInventoryRecord](SoftwareInventoryRecord.md) (5 shared connections)
- [LifecycleIntelligenceService](LifecycleIntelligenceService.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [VersionNormalizationEngine](VersionNormalizationEngine.md) (2 shared connections)
- [calculate_readiness_delta](calculate_readiness_delta.md) (2 shared connections)
- [lifecycle_intelligence.py](lifecycle_intelligence.py.md) (1 shared connections)
- [calculate_scores](calculate_scores.md) (1 shared connections)
- [SessionLocal](SessionLocal.md) (1 shared connections)

## Source Files

- `app/services/cve/cve_enrichment.py`
- `app/services/discovery/aws_ssm_poller.py`
- `app/services/technology_intelligence.py`
- `scripts/validate_delta.py`

## Audit Trail

- EXTRACTED: 51 (93%)
- INFERRED: 4 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
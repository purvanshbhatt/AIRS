import json
from app.services.scoring import calculate_readiness_delta

def run_demo():
    # Base configuration
    assessment_score = 82.0
    previous_score = 84.0

    # 1. Verified Controls (Verification Modifier)
    # We will simulate one verified control just to be thorough, but the prompt highlighted coverage.
    # We'll just pass empty for verification if coverage handles it, but let's include one standard control.
    verified_controls = [
        # The prompt examples focused on Coverage for Crowdstrike and MFA, but we can have a basic control here if needed.
        # Or we can put them directly in Coverage.
    ]

    # 2. Verified Coverages (Coverage Modifier)
    # Verified CrowdStrike coverage
    # Verified MFA coverage
    verified_coverages = [
        {
            "name": "CrowdStrike Agent",
            "family": "Endpoint Protection",
            "coverage_percentage": 98.0
        },
        {
            "name": "Okta MFA",
            "family": "Identity & Access",
            "coverage_percentage": 100.0
        }
    ]

    # 3. Lifecycle Risks (Lifecycle Modifier)
    # EOL PostgreSQL
    lifecycle_risks = [
        {
            "software_name": "PostgreSQL 11",
            "lifecycle_status": "END_OF_LIFE"
        }
    ]

    # 4. Exposure Risks (Exposure Modifier)
    # Internet-facing KEV asset (e.g., Nginx)
    exposure_risks = [
        {
            "software_name": "Nginx",
            "kev_count": 1,
            "is_internet_facing": True,
            "is_critical_asset": False
        }
    ]

    # Execute scoring engine
    result = calculate_readiness_delta(
        assessment_score=assessment_score,
        verified_controls=verified_controls,
        verified_coverages=verified_coverages,
        lifecycle_risks=lifecycle_risks,
        exposure_risks=exposure_risks,
        previous_readiness_score=previous_score
    )

    # Output the payload
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_demo()

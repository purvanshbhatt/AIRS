## Task Assignment for teamwork_preview_challenger_m5_1

**Mission**: Empirical verification & stress testing of build, auth, and staging integration.

**Instructions**:
1. Read `P:\projects\AIRS\.agents\ORIGINAL_REQUEST.md` completely.
2. Execute empirical verification:
   - Run `npm run build` in `P:\projects\AIRS\frontend` and verify exit code 0.
   - Run live staging verification script `py scripts/verify_staging.py` against Cloud Run and Firebase Hosting staging URLs.
   - Test Acme Health Systems demo mode mutation firewall in `api.ts`.
3. Provide verification verdict: APPROVE or REJECT.
4. Write detailed challenger report in your working directory (`P:\projects\AIRS\.agents\teamwork_preview_challenger_m5_1\handoff.md`) and send message to parent.

import sqlite3
from datetime import datetime
import json

def analyze_mttr():
    conn = sqlite3.connect("airs_dev.db")
    cur = conn.cursor()

    # Fetch organization
    org = cur.execute("SELECT id, name FROM organizations LIMIT 1").fetchone()
    if not org:
        print("No organization found.")
        return
    org_id, org_name = org

    # Fetch completed assessments
    assessments = cur.execute(
        "SELECT completed_at, overall_score FROM assessments WHERE organization_id = ? ORDER BY completed_at ASC",
        (org_id,)
    ).fetchall()

    # Fetch audit events for the org
    events = cur.execute(
        "SELECT action, actor, timestamp FROM audit_events WHERE org_id = ? ORDER BY timestamp ASC",
        (org_id,)
    ).fetchall()

    conn.close()

    # Compute MTTR grouped by month
    # We match FINDING_DETECTED and FINDING_RESOLVED for each rule (actor)
    matched_pairs = {}
    for action, actor, ts_str in events:
        ts = datetime.fromisoformat(ts_str)
        if action == "FINDING_DETECTED":
            matched_pairs[actor] = {"detected": ts}
        elif action == "FINDING_RESOLVED":
            if actor in matched_pairs:
                matched_pairs[actor]["resolved"] = ts

    # Group deltas by month
    monthly_deltas = {}
    for rule, times in matched_pairs.items():
        if "detected" in times and "resolved" in times:
            detected = times["detected"]
            resolved = times["resolved"]
            delta_days = (resolved - detected).total_seconds() / 86400.0
            month = detected.strftime("%Y-%m")
            if month not in monthly_deltas:
                monthly_deltas[month] = []
            monthly_deltas[month].append(delta_days)

    # Calculate average MTTR per month
    monthly_mttr = {}
    for month, deltas in monthly_deltas.items():
        monthly_mttr[month] = round(sum(deltas) / len(deltas), 1)

    # Build GHI by month from assessments
    ghi_by_month = {}
    for completed_at, score in assessments:
        month = datetime.fromisoformat(completed_at).strftime("%Y-%m")
        ghi_by_month[month] = score

    # Combine months
    all_months = sorted(set(list(ghi_by_month.keys()) + list(monthly_mttr.keys())))

    # IBM cost of a breach benchmark
    breach_cost = 4450000

    chart_data = []
    for month in all_months:
        mttr = monthly_mttr.get(month, 0.0)
        ghi = ghi_by_month.get(month, 0.0)
        # liability = breach_cost * (1 - GHI/100)
        liability = round((breach_cost * (1 - ghi / 100)) / 1000000.0, 2)
        chart_data.append({
            "month": month,
            "mttrDays": mttr,
            "ghiScore": ghi,
            "liabilityExposureM": liability
        })

    # Calculations for narrative
    start_cycle = chart_data[0]
    end_cycle = chart_data[-1]
    
    mttr_start = start_cycle["mttrDays"]
    mttr_end = end_cycle["mttrDays"]
    ghi_start = start_cycle["ghiScore"]
    ghi_end = end_cycle["ghiScore"]
    liability_start = start_cycle["liabilityExposureM"]
    liability_end = end_cycle["liabilityExposureM"]
    
    liability_reduced = round(liability_start - liability_end, 2)
    mttr_reduction_pct = round(((mttr_start - mttr_end) / mttr_start) * 100, 1)

    # Narrative summary (max 3 sentences)
    narrative = (
        f"By accelerating the Mean Time to Remediation (MTTR) by {mttr_reduction_pct}% (from {mttr_start} to {mttr_end} days), "
        f"the organization successfully drove its Governance Health Index (GHI) from {ghi_start:.0f}% to {ghi_end:.0f}% over three assessment cycles. "
        f"This increased remediation velocity directly correlates to a ${liability_reduced:.2f}M reduction in calculated compliance liability, "
        f"offsetting estimated breach exposure from ${liability_start:.2f}M to ${liability_end:.2f}M."
    )

    output = {
        "narrative": narrative,
        "chartData": chart_data,
        "keyHighlights": [
            f"Remediation latency reduced by {mttr_reduction_pct}% over the last 3 cycles.",
            f"Governance Health Index (GHI) improved by {ghi_end - ghi_start:.0f} points.",
            f"Compliance liability exposure reduced by ${liability_reduced:.2f}M."
        ],
        "metadata": {
            "organization_name": org_name,
            "organization_id": org_id,
            "assessment_count": len(assessments),
            "remediation_velocity_change_pct": mttr_reduction_pct,
            "calculated_at": datetime.now().isoformat()
        }
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    analyze_mttr()

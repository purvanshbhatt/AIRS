import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.clinic.value_metric import ClinicValueMetric
from app.services.clinic_engine.v2.contracts import DailyReadinessReport, ValueSummary

class MetricsEngine:
    """The Value Layer Engine.
    
    Tracks the tangible business value delivered to the clinic.
    This drives renewals by proving ROI automatically.
    """

    def __init__(self, db: Session):
        self.db = db

    def record_daily_metrics(self, org_id: str, report: DailyReadinessReport) -> ClinicValueMetric:
        """Record the value delivered for today based on the readiness report."""
        
        # Calculate derived metrics from the report
        problems_prevented = len(report.failed_checks) + len(report.warnings)
        
        # Simple heuristics for downtime and records protected (these could be more complex in real system)
        downtime_avoided = sum(check.action.estimated_downtime_minutes for check in report.failed_checks if check.action) / 60.0
        
        # 1.5 records per device checked, simplified logic
        records_protected = report.devices_checked * 150 
        
        # Time saved through automated checking (assuming 15 mins per device/account manual check)
        time_saved_mins = (report.devices_checked + report.accounts_checked) * 15

        metric = ClinicValueMetric(
            org_id=org_id,
            metric_date=datetime.now(timezone.utc),
            accounts_protected=report.accounts_checked,
            backups_verified=report.backups_verified,
            devices_protected=report.devices_checked,
            problems_prevented=problems_prevented,
            estimated_downtime_avoided_hours=downtime_avoided,
            estimated_hipaa_records_protected=records_protected,
            estimated_time_saved_minutes=time_saved_mins
        )
        self.db.add(metric)
        self.db.commit()
        return metric

    def get_summary(self, org_id: str, days: int = 30) -> ValueSummary:
        """Aggregate metrics over the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Aggregate logic
        result = self.db.query(
            func.max(ClinicValueMetric.accounts_protected).label("accounts"),
            func.max(ClinicValueMetric.devices_protected).label("devices"),
            func.sum(ClinicValueMetric.backups_verified).label("backups"),
            func.sum(ClinicValueMetric.problems_prevented).label("problems"),
            func.sum(ClinicValueMetric.estimated_downtime_avoided_hours).label("downtime"),
            func.max(ClinicValueMetric.estimated_hipaa_records_protected).label("hipaa"),
            func.sum(ClinicValueMetric.estimated_time_saved_minutes).label("time_saved")
        ).filter(
            ClinicValueMetric.org_id == org_id,
            ClinicValueMetric.metric_date >= cutoff_date
        ).first()

        # Handle empty cases
        if not result or result[0] is None:
            return ValueSummary(period_label=f"Last {days} Days")

        return ValueSummary(
            period_label=f"Last {days} Days",
            accounts_protected=result.accounts or 0,
            devices_protected=result.devices or 0,
            backups_verified=result.backups or 0,
            problems_prevented=result.problems or 0,
            estimated_downtime_avoided_hours=result.downtime or 0.0,
            estimated_hipaa_records_protected=result.hipaa or 0,
        )

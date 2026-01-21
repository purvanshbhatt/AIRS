"""
Report service - business logic for persistent report generation and management.

All operations are scoped by owner_uid for tenant isolation.
Reports store a snapshot of assessment data at generation time for consistency.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.report import Report
from app.models.assessment import Assessment
from app.models.organization import Organization
from app.schemas.report import (
    ReportCreate,
    ReportType,
    ReportSnapshot,
    DomainScoreSnapshot,
    FindingSnapshot,
)
from app.services.assessment import AssessmentService


class ReportService:
    """Service for report operations with tenant isolation."""
    
    def __init__(self, db: Session, owner_uid: str):
        """
        Initialize service.
        
        Args:
            db: Database session
            owner_uid: Firebase user UID for tenant isolation (required)
        """
        if not owner_uid:
            raise ValueError("owner_uid is required for report operations")
        self.db = db
        self.owner_uid = owner_uid
    
    def _base_query(self):
        """Get base query filtered by owner_uid."""
        return self.db.query(Report).filter(Report.owner_uid == self.owner_uid)
    
    def create(self, assessment_id: str, data: ReportCreate) -> Report:
        """
        Generate and save a new report for an assessment.
        
        Args:
            assessment_id: ID of the assessment to generate report for
            data: Report creation parameters
            
        Returns:
            Created Report object
            
        Raises:
            ValueError: If assessment not found or not owned by user
        """
        # Use AssessmentService to get assessment with tenant isolation
        assessment_service = AssessmentService(self.db, self.owner_uid)
        assessment = assessment_service.get(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")
        
        # Get organization
        org = self.db.query(Organization).filter(
            Organization.id == assessment.organization_id,
            Organization.owner_uid == self.owner_uid
        ).first()
        if not org:
            raise ValueError(f"Organization not found for assessment: {assessment_id}")
        
        # Get full summary for snapshot
        summary = assessment_service.get_summary(assessment_id)
        if not summary:
            raise ValueError(f"Could not generate summary for assessment: {assessment_id}")
        
        # Build snapshot
        snapshot = self._build_snapshot(assessment, org, summary)
        
        # Generate title if not provided
        title = data.title or f"{org.name} - {assessment.title or 'Assessment'} Report"
        
        # Create report record
        report = Report(
            owner_uid=self.owner_uid,
            organization_id=assessment.organization_id,
            assessment_id=assessment_id,
            report_type=data.report_type.value,
            title=title,
            snapshot=snapshot.model_dump_json(),
            overall_score=summary.get("overall_score"),
            maturity_level=summary.get("tier", {}).get("maturity_level") if isinstance(summary.get("tier"), dict) else None,
            maturity_name=summary.get("tier", {}).get("label") if isinstance(summary.get("tier"), dict) else None,
            findings_count=summary.get("findings_count", 0),
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def _build_snapshot(
        self, 
        assessment: Assessment, 
        org: Organization, 
        summary: Dict[str, Any]
    ) -> ReportSnapshot:
        """Build a point-in-time snapshot of assessment data."""
        
        # Build domain scores
        domain_scores = []
        for ds in summary.get("domain_scores", []):
            domain_scores.append(DomainScoreSnapshot(
                domain_id=ds.get("domain_id", ""),
                domain_name=ds.get("domain_name", ""),
                score=ds.get("score", 0),
                score_5=ds.get("score_5", 0),
                weight=ds.get("weight", 0),
                earned_points=ds.get("earned_points"),
                max_points=ds.get("max_points"),
            ))
        
        # Build findings
        findings = []
        for f in summary.get("findings", []):
            findings.append(FindingSnapshot(
                id=f.get("id", ""),
                title=f.get("title", ""),
                severity=f.get("severity", "medium"),
                domain=f.get("domain"),
                evidence=f.get("evidence"),
                recommendation=f.get("recommendation"),
                description=f.get("description"),
            ))
        
        # Get tier info
        tier = summary.get("tier", {})
        maturity_level = tier.get("maturity_level", 1) if isinstance(tier, dict) else 1
        maturity_name = tier.get("label", "Initial") if isinstance(tier, dict) else "Initial"
        
        return ReportSnapshot(
            assessment_id=assessment.id,
            assessment_title=assessment.title,
            organization_id=org.id,
            organization_name=org.name,
            overall_score=summary.get("overall_score", 0),
            maturity_level=maturity_level,
            maturity_name=maturity_name,
            domain_scores=domain_scores,
            findings=findings,
            findings_count=summary.get("findings_count", 0),
            critical_high_count=summary.get("critical_high_count", 0),
            baseline_selected=None,  # Can be set if user selects baseline
            baseline_profiles=summary.get("baseline_profiles"),
            llm_enabled=summary.get("llm_enabled"),
            llm_provider=summary.get("llm_provider"),
            llm_model=summary.get("llm_model"),
            llm_mode=summary.get("llm_mode"),
            executive_summary=summary.get("executive_summary_text"),
            roadmap_narrative=summary.get("roadmap_narrative_text"),
            rubric_version="1.0.0",  # TODO: Get from rubric
            generated_at=datetime.utcnow(),
        )
    
    def get(self, report_id: str) -> Optional[Report]:
        """Get report by ID (scoped to current user)."""
        return self._base_query().filter(Report.id == report_id).first()
    
    def get_with_snapshot(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report with parsed snapshot data."""
        report = self.get(report_id)
        if not report:
            return None
        
        # Get org name for response
        org = self.db.query(Organization).filter(
            Organization.id == report.organization_id
        ).first()
        
        # Get assessment title for response
        assessment = self.db.query(Assessment).filter(
            Assessment.id == report.assessment_id
        ).first()
        
        # Parse snapshot
        try:
            snapshot_data = json.loads(report.snapshot)
        except json.JSONDecodeError:
            snapshot_data = {}
        
        return {
            "id": report.id,
            "owner_uid": report.owner_uid,
            "organization_id": report.organization_id,
            "organization_name": org.name if org else None,
            "assessment_id": report.assessment_id,
            "assessment_title": assessment.title if assessment else None,
            "report_type": report.report_type,
            "title": report.title,
            "overall_score": report.overall_score,
            "maturity_level": report.maturity_level,
            "maturity_name": report.maturity_name,
            "findings_count": report.findings_count,
            "created_at": report.created_at,
            "snapshot": snapshot_data,
        }
    
    def list(
        self,
        organization_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
        report_type: Optional[ReportType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Report], int]:
        """
        List reports with optional filters (scoped to current user).
        
        Returns:
            Tuple of (reports list, total count)
        """
        query = self._base_query()
        
        # Apply filters
        if organization_id:
            query = query.filter(Report.organization_id == organization_id)
        if assessment_id:
            query = query.filter(Report.assessment_id == assessment_id)
        if report_type:
            query = query.filter(Report.report_type == report_type.value)
        if start_date:
            query = query.filter(Report.created_at >= start_date)
        if end_date:
            query = query.filter(Report.created_at <= end_date)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        reports = query.order_by(desc(Report.created_at)).offset(offset).limit(limit).all()
        
        return reports, total
    
    def delete(self, report_id: str) -> bool:
        """Delete a report (scoped to current user)."""
        report = self.get(report_id)
        if not report:
            return False
        
        # TODO: If storage_path exists, delete the stored file
        
        self.db.delete(report)
        self.db.commit()
        return True

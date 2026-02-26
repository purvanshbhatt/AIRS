"""
Tech Stack service — business logic for tech stack lifecycle tracking.
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.tech_stack import TechStackItem, LtsStatus
from app.schemas.tech_stack import (
    TechStackItemCreate,
    TechStackItemUpdate,
    TechStackItemResponse,
    TechStackSummary,
)

logger = logging.getLogger(__name__)

# ── Risk classification rules ────────────────────────────────────────
RISK_RULES = {
    "eol": "critical",          # End-of-life = critical risk
    "deprecated": "high",       # Deprecated = high risk
}

MAJOR_VERSIONS_HIGH = 3         # 3+ major versions behind = high risk
MAJOR_VERSIONS_MEDIUM = 1       # 1-2 major versions behind = medium


class TechStackService:
    """Service for tech stack lifecycle management."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def create(self, data: TechStackItemCreate) -> TechStackItem:
        """Create a new tech stack item."""
        item = TechStackItem(
            org_id=self.org_id,
            component_name=data.component_name,
            version=data.version,
            lts_status=LtsStatus(data.lts_status),
            major_versions_behind=data.major_versions_behind,
            category=data.category,
            notes=data.notes,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get(self, item_id: str) -> Optional[TechStackItem]:
        """Get a single item by ID."""
        return (
            self.db.query(TechStackItem)
            .filter(
                TechStackItem.id == item_id,
                TechStackItem.org_id == self.org_id,
            )
            .first()
        )

    def list_all(self) -> List[TechStackItem]:
        """List all tech stack items for the org, ordered by risk."""
        return (
            self.db.query(TechStackItem)
            .filter(TechStackItem.org_id == self.org_id)
            .order_by(TechStackItem.major_versions_behind.desc())
            .all()
        )

    def update(self, item_id: str, data: TechStackItemUpdate) -> Optional[TechStackItem]:
        """Update an existing item."""
        item = self.get(item_id)
        if not item:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "lts_status" in update_data:
            update_data["lts_status"] = LtsStatus(update_data["lts_status"])
        for key, value in update_data.items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: str) -> bool:
        """Delete an item."""
        item = self.get(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    @staticmethod
    def classify_risk(item: TechStackItem) -> str:
        """Classify risk level for a single tech stack item."""
        status_str = item.lts_status.value if isinstance(item.lts_status, LtsStatus) else item.lts_status

        # EOL or Deprecated overrides version gap
        if status_str in RISK_RULES:
            return RISK_RULES[status_str]

        # Version gap rules
        if item.major_versions_behind >= MAJOR_VERSIONS_HIGH:
            return "high"
        elif item.major_versions_behind >= MAJOR_VERSIONS_MEDIUM:
            return "medium"

        return "low"

    def enrich_response(self, item: TechStackItem) -> TechStackItemResponse:
        """Convert model to response with computed risk_level."""
        return TechStackItemResponse(
            id=item.id,
            org_id=item.org_id,
            component_name=item.component_name,
            version=item.version,
            lts_status=item.lts_status.value if isinstance(item.lts_status, LtsStatus) else item.lts_status,
            major_versions_behind=item.major_versions_behind,
            category=item.category,
            notes=item.notes,
            risk_level=self.classify_risk(item),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def get_summary(self, items: Optional[List[TechStackItem]] = None) -> TechStackSummary:
        """Generate a summary of the full tech stack."""
        if items is None:
            items = self.list_all()

        eol_count = 0
        deprecated_count = 0
        outdated_count = 0
        risk_breakdown: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for item in items:
            status_str = item.lts_status.value if isinstance(item.lts_status, LtsStatus) else item.lts_status
            if status_str == "eol":
                eol_count += 1
            elif status_str == "deprecated":
                deprecated_count += 1
            if item.major_versions_behind >= MAJOR_VERSIONS_MEDIUM:
                outdated_count += 1

            risk = self.classify_risk(item)
            risk_breakdown[risk] = risk_breakdown.get(risk, 0) + 1

        # Deterministic summary (no LLM)
        parts = []
        if eol_count:
            parts.append(f"{eol_count} EOL component{'s' if eol_count != 1 else ''} requiring immediate migration")
        if deprecated_count:
            parts.append(f"{deprecated_count} deprecated component{'s' if deprecated_count != 1 else ''}")
        if outdated_count:
            parts.append(f"{outdated_count} component{'s' if outdated_count != 1 else ''} behind on major versions")
        if not parts:
            summary = "All components are current. No lifecycle risks detected."
        else:
            summary = ". ".join(parts) + "."

        return TechStackSummary(
            eol_count=eol_count,
            deprecated_count=deprecated_count,
            outdated_count=outdated_count,
            risk_breakdown=risk_breakdown,
            upgrade_governance_summary=summary,
        )

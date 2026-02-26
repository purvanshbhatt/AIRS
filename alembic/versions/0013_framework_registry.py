"""add_framework_registry

Revision ID: 0013_framework_registry
Revises: 0012_governance_expansion
Create Date: 2025-07-15

Adds:
- framework_registry table with canonical framework definitions
- Seeds 12 frameworks from the compliance engine
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0013_framework_registry"
down_revision: str = "0012_governance_expansion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Seed data — canonical frameworks from the compliance engine ──────
SEED_FRAMEWORKS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "hipaa")),
        "name": "HIPAA",
        "full_name": "Health Insurance Portability and Accountability Act",
        "category": "regulatory",
        "version": None,
        "description": "U.S. federal law protecting health information privacy and security.",
        "reference_url": "https://www.hhs.gov/hipaa/index.html",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "cmmc-l2")),
        "name": "CMMC Level 2",
        "full_name": "Cybersecurity Maturity Model Certification Level 2",
        "category": "regulatory",
        "version": "2.0",
        "description": "DoD cybersecurity standard for contractors handling CUI.",
        "reference_url": "https://dodcio.defense.gov/CMMC/",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "nist-800-171")),
        "name": "NIST SP 800-171",
        "full_name": "NIST Special Publication 800-171",
        "category": "regulatory",
        "version": "r2",
        "description": "Protecting Controlled Unclassified Information in nonfederal systems.",
        "reference_url": "https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "pci-dss")),
        "name": "PCI-DSS v4.0",
        "full_name": "Payment Card Industry Data Security Standard",
        "category": "contractual",
        "version": "4.0",
        "description": "Security standard for organizations handling cardholder data.",
        "reference_url": "https://www.pcisecuritystandards.org/",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "gdpr")),
        "name": "GDPR",
        "full_name": "General Data Protection Regulation",
        "category": "regulatory",
        "version": None,
        "description": "EU regulation on data protection and privacy.",
        "reference_url": "https://gdpr.eu/",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "nist-privacy")),
        "name": "NIST Privacy Framework",
        "full_name": "NIST Privacy Framework",
        "category": "voluntary",
        "version": "1.0",
        "description": "Voluntary framework for managing privacy risk.",
        "reference_url": "https://www.nist.gov/privacy-framework",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "soc2-type2")),
        "name": "SOC 2 Type II",
        "full_name": "System and Organization Controls 2 Type II",
        "category": "contractual",
        "version": None,
        "description": "Trust services criteria for service organizations.",
        "reference_url": "https://www.aicpa.org/soc2",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "nist-ai-rmf")),
        "name": "NIST AI RMF",
        "full_name": "NIST Artificial Intelligence Risk Management Framework",
        "category": "voluntary",
        "version": "1.0",
        "description": "Framework for managing risks in AI systems.",
        "reference_url": "https://www.nist.gov/artificial-intelligence/ai-risk-management-framework",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "nist-csf")),
        "name": "NIST CSF 2.0",
        "full_name": "NIST Cybersecurity Framework 2.0",
        "category": "voluntary",
        "version": "2.0",
        "description": "Cybersecurity risk management framework for critical infrastructure.",
        "reference_url": "https://www.nist.gov/cyberframework",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "ffiec")),
        "name": "FFIEC IT Handbook",
        "full_name": "Federal Financial Institutions Examination Council IT Handbook",
        "category": "regulatory",
        "version": None,
        "description": "IT examination guidance for financial institutions.",
        "reference_url": "https://ithandbook.ffiec.gov/",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "fedramp")),
        "name": "FedRAMP",
        "full_name": "Federal Risk and Authorization Management Program",
        "category": "regulatory",
        "version": None,
        "description": "Standardized approach to security assessment for cloud services used by federal agencies.",
        "reference_url": "https://www.fedramp.gov/",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "iso-27001")),
        "name": "ISO 27001",
        "full_name": "ISO/IEC 27001 Information Security Management",
        "category": "voluntary",
        "version": "2022",
        "description": "International standard for information security management systems.",
        "reference_url": "https://www.iso.org/isoiec-27001-information-security.html",
    },
]


def upgrade() -> None:
    # Create framework_registry table
    op.create_table(
        "framework_registry",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.Enum("regulatory", "contractual", "voluntary", name="frameworkcategory"),
            nullable=False,
        ),
        sa.Column("version", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # Seed canonical frameworks
    framework_table = sa.table(
        "framework_registry",
        sa.column("id", sa.CHAR(36)),
        sa.column("name", sa.String),
        sa.column("full_name", sa.String),
        sa.column("category", sa.String),
        sa.column("version", sa.String),
        sa.column("description", sa.Text),
        sa.column("reference_url", sa.String),
    )
    op.bulk_insert(framework_table, SEED_FRAMEWORKS)


def downgrade() -> None:
    op.drop_table("framework_registry")

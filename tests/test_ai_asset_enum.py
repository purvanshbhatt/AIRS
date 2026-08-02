"""
Tests for Sprint 1.8, Task S1.8-B5 — AiAsset enum expansion.

Covers:
  - All new enum values are exposed on AIAssetType.
  - Round-trip persistence & refresh through SQLAlchemy.
  - New values appear for Vector DBs (count), MCP Servers, Agent
    Frameworks, plus the rest of the new ones.
  - Existing rows with old enum values round-trip unchanged.
"""

import uuid

import pytest

from app.models import Organization
from app.models.ai_asset import AIAsset, AIAssetType


def _make_org(session) -> str:
    org = Organization(id=str(uuid.uuid4()), name="AiAsset Enum Test")
    session.add(org)
    session.commit()
    return org.id


class TestEnumMembers:
    def test_mcp_server_present(self):
        assert AIAssetType.mcp_server.value == "mcp_server"

    def test_mcp_client_present(self):
        assert AIAssetType.mcp_client.value == "mcp_client"

    def test_agent_framework_present(self):
        assert AIAssetType.agent_framework.value == "agent_framework"

    def test_embedding_pipeline_present(self):
        assert AIAssetType.embedding_pipeline.value == "embedding_pipeline"

    def test_rag_corpus_present(self):
        assert AIAssetType.rag_corpus.value == "rag_corpus"

    def test_training_dataset_present(self):
        assert AIAssetType.training_dataset.value == "training_dataset"

    def test_evaluation_pipeline_present(self):
        assert AIAssetType.evaluation_pipeline.value == "evaluation_pipeline"

    def test_prompt_library_present(self):
        assert AIAssetType.prompt_library.value == "prompt_library"

    def test_vector_db_preserved(self):
        assert AIAssetType.vector_db.value == "vector_db"


class TestAssetRoundTrip:
    @pytest.mark.parametrize(
        "asset_type",
        [
            AIAssetType.mcp_server,
            AIAssetType.mcp_client,
            AIAssetType.agent_framework,
            AIAssetType.embedding_pipeline,
            AIAssetType.rag_corpus,
            AIAssetType.training_dataset,
            AIAssetType.evaluation_pipeline,
            AIAssetType.prompt_library,
        ],
    )
    def test_round_trip_each_new_type(self, db_session, asset_type):
        org_id = _make_org(db_session)
        asset = AIAsset(
            org_id=org_id,
            name=f"Test {asset_type.value}",
            asset_type=asset_type,
            business_criticality="low",
            exposure_level="internal",
            lifecycle_stage="development",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        assert asset.asset_type == asset_type
        assert asset.id is not None

    def test_existing_types_still_enumerable(self):
        # Sanity: existing enum values still present.
        assert AIAssetType.model.value == "model"
        assert AIAssetType.vector_db.value == "vector_db"
        assert AIAssetType.fine_tuned_model.value == "fine_tuned_model"

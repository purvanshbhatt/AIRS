"""API routes for Logic Firewall deterministic prompt-injection defense."""

from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import User, require_auth
from app.schemas.logic_firewall import (
    LogicFirewallSimulationRequest,
    LogicFirewallSimulationResponse,
    LogicTraceResponse,
    QuarantinedChunkResponse,
)
from app.services.logic_firewall import (
    build_simulated_retrieval_chunks,
    get_logic_firewall_service,
    render_raw_llm_like_answer,
    render_safe_answer,
)

router = APIRouter()
logger = logging.getLogger("airs.logic_firewall")


@router.post("/simulate", response_model=LogicFirewallSimulationResponse)
async def run_logic_firewall_simulation(
    payload: LogicFirewallSimulationRequest,
    user: User = Depends(require_auth),
):
    """
    Run deterministic prompt-injection simulation for the AI Attack Simulation Lab.
    """
    request_id = f"lf-{uuid4().hex[:12]}"
    service = get_logic_firewall_service()
    retrieved_chunks = build_simulated_retrieval_chunks()

    raw_answer = render_raw_llm_like_answer(retrieved_chunks, payload.query)

    safe_chunks = retrieved_chunks
    quarantined = []
    if payload.enable_logic_firewall:
        safe_chunks, quarantined = service.logic_firewall(retrieved_chunks)

    safe_answer = render_safe_answer(safe_chunks, payload.query)

    all_signals = sorted({signal for q in quarantined for signal in q.signals})
    confidence = max((q.confidence for q in quarantined), default=0.94)
    service.store_trace(
        request_id=request_id,
        signals=all_signals or ["Semantic Divergence Detected"],
        confidence=confidence,
    )
    stored_trace = service.get_trace(request_id)

    logger.info(
        "logic_firewall.detected request_id=%s owner_uid=%s threat_type=%s mitre_mapping=%s quarantined=%s",
        request_id,
        user.uid,
        "Poisoned Retrieval",
        "AML.T0031",
        len(quarantined),
    )

    return LogicFirewallSimulationResponse(
        request_id=request_id,
        scenario=f"{payload.organization_name} - Compromised HR Knowledge Base",
        query=payload.query,
        pipeline="[Retrieval Layer] -> [Logic Firewall] -> [LLM (Gemini)] -> [Response]",
        raw_response_without_firewall=raw_answer,
        sanitized_response_with_firewall=safe_answer,
        chunks_total=len(retrieved_chunks),
        chunks_quarantined=len(quarantined),
        quarantined_chunks=[
            QuarantinedChunkResponse(
                chunk_index=item.chunk_index,
                threat_type=item.threat_type,
                mitre_mapping=item.mitre_mapping,
                signals=item.signals,
                action=item.action,
                confidence=item.confidence,
                excerpt=item.excerpt,
            )
            for item in quarantined
        ],
        threat_type="Poisoned Retrieval (AML.T0031)",
        signal="Semantic Divergence Detected",
        actions_taken=[
            "Chunk Quarantined",
            "Injection Blocked",
            "SOC Alert Triggered",
        ],
        logic_trace=LogicTraceResponse(
            request_id=request_id,
            threat_type="Poisoned Retrieval",
            mitre_mapping="AML.T0031",
            signals=all_signals or ["Semantic Divergence Detected"],
            action="quarantine_chunk",
            confidence=confidence,
            created_at=stored_trace.created_at if stored_trace else "",
        ),
        frameworks={
            "nist_ai_rmf": "Measure / Manage",
            "nist_csf": "DE.CM (Detection)",
            "owasp_llm_top10": "Prompt Injection",
        },
        business_impact_narrative=(
            "ResilAI prevented a prompt injection attack that could have redirected "
            "employees to a credential harvesting domain, reducing phishing exposure "
            "and potential identity compromise risk."
        ),
    )


@router.get("/trace/{request_id}", response_model=LogicTraceResponse)
async def get_logic_firewall_trace(
    request_id: str,
    user: User = Depends(require_auth),
):
    """Return deterministic logic trace for a simulation request ID."""
    service = get_logic_firewall_service()
    trace = service.get_trace(request_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace not found for request_id: {request_id}",
        )

    return LogicTraceResponse(
        request_id=trace.request_id,
        threat_type=trace.threat_type,
        mitre_mapping=trace.mitre_mapping,
        signals=trace.signals,
        action=trace.action,
        confidence=trace.confidence,
        created_at=trace.created_at,
    )

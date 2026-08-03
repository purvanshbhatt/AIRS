# Agentic Operations Architecture Diagram

This document serves as the specification for the visual architecture diagram to be included in the Hackathon submission. The diagram must illustrate the strict architectural boundaries that keep ResilAI enterprise-grade while integrating Splunk.

## Diagram Flow

```mermaid
graph TD
    subgraph Customer Environment
        SE[Splunk Enterprise] --> |Webhook / MCP| SEE
    end

    subgraph ResilAI Platform
        subgraph Sentinel Module
            SEE[Sentinel Evidence Engine]
            DT[Digital Twin Simulator]
            BI[Board Intelligence]
        end
        
        subgraph Core AIRS Engine
            ASE[AIRS Scoring Engine]
            RM[Rubric Mappings]
        end
    end

    subgraph Output
        ER[Executive Report]
    end

    %% Data Flow
    SEE -.->|Maps Telemetry to Generic Evidence| ASE
    ASE -.->|Resolves Framework & Math| DT
    DT -.->|Executes Zero-Mutation Scenario| ASE
    ASE -.->|Returns Score Drop| BI
    BI -.->|Generates Narrative| ER
```

## Key Narrative Elements
When drawing or presenting this architecture, emphasize the following points to the judges:
1. **Separation of Concerns:** Sentinel handles *Translation*, AIRS Core handles *Scoring*. 
2. **Zero-Mutation:** The Digital Twin creates isolated in-memory replicas of assessments to run scenarios, ensuring production data is never contaminated.
3. **Deterministic Constraints:** Gemini (Board Intelligence) is structurally prevented from hallucinating scores because the math is executed strictly by AIRS *before* hitting the LLM.

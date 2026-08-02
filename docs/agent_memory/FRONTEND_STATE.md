# Frontend State

Core Layer: React (18.3.1), Vite (6.4.1), TypeScript (5.5.3), TailwindCSS (4.1.18)
Client Router: React Router
API Client: `frontend/src/api.ts`

Recent Changes:
- Implemented Evidence Confidence widget, verified timeline, and connectors grid in `EvidenceNetwork.tsx` (Epic C).
- Integrated real-time GHI metrics and confidence score gauge in the Dashboard (Dashboard.tsx).
- Created `BoardStory.tsx` boardroom narrative briefing with 10 sections and fallback modes (Epic D).
- Created `DecisionEngine.tsx` postural ROI & Decision Simulator with action toggling & projection (Epic D).
- Created `BusinessUnits.tsx` departmental risk heatmap based on GHI parameters.
- Implemented `PersonaSwitcher` persona-based view filtering on the Dashboard (Executive vs Forensic).
- Cleaned up orphaned dashboard routes (SentinelDashboard, PilotDashboard) and saved backup configs in `.deprecated_routes.txt`.
- Bounded build checks confirmed 100% green TypeScript compilation and production packaging.

Next Tasks:
- All current sprint and backlog items fully implemented. Bounded verification is complete.

# ResilAI Entitlements and Access Granting Flow

This document defines the end-to-end access granting model, subscription paywall enforcement, and account isolation across ResilAI environments.

---

## 1. Access Model & Customer Progression

ResilAI enforces a strict four-stage access model:

| User State | Access Level | Data Boundary |
| :--- | :--- | :--- |
| **Visitor** | Marketing site, Pricing, Public Docs, Public Demo link | No organization or auth context |
| **Demo User** | Sandboxed simulated clinic workspace (`Acme Health Systems`) | Frozen synthetic data; read-only simulated actions |
| **Registered (Unpaid)** | Account profile, Organization overview, Preview schemas | No live infrastructure, no telemetry ingestion, no executive dossiers |
| **Design Partner / Subscriber** | Full product access, AWS & SIEM connectors, Continuous scoring | Live encrypted credentials, real telemetry feeds, immutable evidence ledger |

> [!IMPORTANT]
> **Core Tenet**: *Demo access is free. Product access is paid.*  
> Paywall gates are enforced **in the backend** via FastAPI authorization dependencies (`require_entitlement`), returning structured `HTTP 402 Payment Required` payloads when an organization lacks a capability.

---

## 2. Entitlements Hierarchy

Entitlements are mapped directly to subscription plans in `app/services/billing/entitlements.py`:

```mermaid
flowchart TD
    Free["Free / Unpaid Tier"] --> DP["Design Partner Tier"]
    DP --> Growth["Growth Tier"]
    Growth --> Enterprise["Enterprise Tier"]

    subgraph "Free Tier Capabilities"
        Free --- C1["demo_access"]
        Free --- C2["simulated_data"]
        Free --- C3["public_product_preview"]
        Free --- C4["account_management"]
    end

    subgraph "Design Partner Capabilities"
        DP --- C5["real_organization"]
        DP --- C6["telemetry_ingestion"]
        DP --- C7["evidence_collection"]
        DP --- C8["readiness_scoring"]
        DP --- C9["connectors_manage"]
        DP --- C10["executive_reports"]
    end

    subgraph "Growth Capabilities"
        Growth --- C11["api_keys"]
        Growth --- C12["webhooks"]
        Growth --- C13["advanced_reporting"]
        Growth --- C14["additional_users"]
    end

    subgraph "Enterprise Capabilities"
        Enterprise --- C15["advanced_integrations"]
        Enterprise --- C16["enterprise_controls"]
        Enterprise --- C17["custom_frameworks"]
    end
```

---

## 3. Paywall Enforcement Architecture

### Backend Enforcement (`app/core/entitlements.py`)
- Endpoints protecting live assets (e.g., `POST /api/v1/connectors`, `POST /api/v1/telemetry/events`, `POST /api/agent-audits`) declare:
  ```python
  _ent: None = Depends(require_entitlement(Entitlement.CONNECTORS_MANAGE))
  ```
- If the caller's organization lacks the entitlement, the middleware returns `HTTP 402` with structured error metadata:
  ```json
  {
    "error": {
      "code": "PAYMENT_REQUIRED",
      "message": "An active ResilAI subscription is required to access this feature.",
      "required_entitlement": "connectors_manage",
      "current_plan": "free",
      "upgrade_url": "/pricing",
      "request_id": "req-xyz-123"
    }
  }
  ```

### Administrator & Testing Bypass
- Accounts owned by or matching administrator identities (`purvansh95b@gmail.com`, `purvansh@resilai.org`, or `@resilai.org` domain) automatically bypass paywall checks.
- In both `app/core/entitlements.py` and `EntitlementService.is_exempt_org()`, administrator-owned organizations are granted `enterprise` tier capabilities immediately.
- Frontend `useCapabilities` verifies administrator email and activates full capabilities on the client side to prevent false-positive lock states during testing.

---

## 4. End-to-End Subscription Access Granting Flow

When a user encounters a paywalled feature (such as the AWS Security Hub connector):

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer / Admin
    participant UI as ResilAI Frontend (/connectors)
    participant Modal as Connector Setup Modal
    participant Pricing as Pricing Page (/pricing)
    participant API as FastAPI Backend (/api)
    participant DB as Postgres + Firestore

    User->>UI: Clicks "Setup" on AWS Connector
    UI->>Modal: Opens Configuration Modal
    alt Org is Unpaid
        Modal-->>User: Displays "Active Subscription Required" Banner + "Go to Subscription & Pricing" Button
        User->>Modal: Clicks "Go to Subscription & Pricing"
        Modal->>Pricing: Navigates to /pricing
        Pricing-->>User: Displays Workspace Info & "Activate Design Partner Plan" Button
        User->>Pricing: Clicks "Activate Design Partner Plan (Instant Access)"
        Pricing->>API: POST /api/orgs/{org_id}/billing/activate { plan: "design-partner" }
        API->>DB: Updates org.subscription_plan="design-partner", org.subscription_status="active"
        DB-->>API: Persisted (Postgres + Firestore cold-start sync)
        API-->>Pricing: 200 OK { success: true, plan: "design-partner" }
        Pricing->>UI: Refreshes capabilities & redirects to /connectors
        UI-->>User: Toast: "Plan Activated! Live connectors unlocked."
        User->>Modal: Completes AWS IAM Role ARN registration
        Modal->>API: POST /api/v1/connectors { connector_type: "aws", ... }
        API-->>Modal: 201 Created (Encrypted credentials saved)
    end
```

---

## 5. Production Stripe Webhook Integration

For self-service production subscriptions:
1. **Checkout**: The customer selects Growth or Enterprise on `/pricing` and is redirected to Stripe Checkout.
2. **Webhook**: Stripe sends `checkout.session.completed` to `POST /api/billing/webhook`.
3. **Activation**: `CheckoutService._handle_checkout_completed()` matches `org_id` from metadata, commits active subscription status to PostgreSQL, and dual-writes to Cloud Firestore.
4. **Instant Unlock**: Next client API request immediately passes `require_entitlement` checks.

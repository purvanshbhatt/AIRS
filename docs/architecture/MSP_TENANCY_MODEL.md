# MSP Tenancy Architecture Model

## 1. Goal
Define the logical relationship between Clinic → MSP → ResilAI to support cross-tenant management in the future.

## 2. Relationships

The core tenancy model relies on two new fields in the `Organization` model:
- `parent_org_id`: Used when a large healthcare organization has multiple sub-clinics, operating as a conglomerate.
- `managed_by_msp_id`: Used when an external Managed Service Provider (MSP) manages the IT and compliance for the clinic.

### 2.1 Clinic-Centric Model (Direct)
A standard single clinic using ResilAI directly.
- `org_id`: `clinic_A`
- `parent_org_id`: `null`
- `managed_by_msp_id`: `null`

### 2.2 Conglomerate Model (Parent-Child)
A large healthcare network (Parent) with multiple regional clinics (Children).
- **Parent:**
  - `org_id`: `health_network_X`
  - `parent_org_id`: `null`
- **Child:**
  - `org_id`: `clinic_B`
  - `parent_org_id`: `health_network_X`

The Parent organization has visibility into all Child organizations, rolling up readiness scores into a master Executive Dashboard.

### 2.3 MSP Model (Managed Service Provider)
An MSP that manages multiple independent clinics. The MSP itself has an organization profile in ResilAI.
- **MSP:**
  - `org_id`: `msp_secure_health`
- **Clinic 1:**
  - `org_id`: `clinic_C`
  - `managed_by_msp_id`: `msp_secure_health`
- **Clinic 2:**
  - `org_id`: `clinic_D`
  - `managed_by_msp_id`: `msp_secure_health`

The MSP receives a unified **MSP Dashboard** allowing them to switch contexts between managed clinics, aggregate vulnerabilities across their portfolio, and perform cross-tenant bulk remediations (e.g., updating a baseline policy across all managed clinics).

## 3. Security & Isolation
- **Tenant Boundary:** The `org_id` remains the primary isolation boundary. All queries, connectors, and evidence are strictly bound to the `org_id`.
- **RBAC (Role-Based Access Control):** 
  - Users belonging to `managed_by_msp_id` with `msp_admin` roles are granted dynamic access to assume the context of `clinic_C`.
  - The clinic retains ownership of their data and can revoke the MSP's access by nullifying the `managed_by_msp_id`.

## 4. API & Connector Implications
- Connectors (e.g., Wazuh, CrowdStrike) configured at the `msp_secure_health` level can be authorized to pull telemetry for `clinic_C` if the API key used by the MSP supports multi-tenancy on the vendor's side. 
- If not, the MSP must configure individual connector credentials within the context of each clinic's `org_id`.

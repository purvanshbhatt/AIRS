# ResilAI — Clinic Pilot Operational Guide

## 🏥 Clinic Onboarding & Execution

This guide outlines step-by-step instructions for deploying ResilAI in a clinic environment.

---

## 📋 Prerequisites

1. **Microsoft 365 Global Admin** or App Registration credentials (`Client ID`, `Client Secret`, `Tenant ID`).
2. **Veeam Backup & Replication v11/v12** REST API access or API Token.
3. **Wazuh Manager** API Endpoint (optional).

---

## 🛠️ Step 1: Connect Integrations

1. Navigate to `/dashboard/clinic/integrations`.
2. Click **Connect Microsoft 365** and authenticate via OAuth 2.0.
3. Add Veeam REST API URL and Service Account credentials.
4. Verify that connection badges turn **Active (Green)**.

---

## 🏥 Step 2: Configure Clinic Moments

1. Open `/dashboard/clinic/onboarding`.
2. Register key medical devices (e.g., Ultrasound Workstation, EHR Terminal).
3. Set recovery RTO/RPO expectations.
4. Trigger baseline **Clinic Moment Evaluation**.

# ResilAI Product Guide

This guide explains how ResilAI works to protect your clinic, designed specifically for clinic owners, healthcare executives, and operations leaders.

---

## 1. What Is ResilAI?

ResilAI is an automated verification system that ensures your clinic is ready to operate safely every day.

**What ResilAI does:**
ResilAI checks whether the security protections a business already relies on are actually working and producing evidence. It connects to the tools your IT team has already set up (like Microsoft, backup systems, and antivirus) and verifies that they are active, updated, and protecting your patient data.

**What problem it solves:**
Many clinics suffer data breaches or ransomware attacks despite having purchased security software, simply because the software was silently turned off, misconfigured, or broken. ResilAI finds these silent failures before attackers do.

**What it does NOT do:**
ResilAI is not an IT helpdesk, and it does not replace your IT team. It is an independent auditor that works alongside your IT provider to ensure nothing slips through the cracks.

**Why verification matters:**
Assuming you are protected is dangerous. Only continuous, automated verification can provide the confidence you need to safely open your clinic doors each morning.

---

## 2. How ResilAI Works

ResilAI operates in a continuous loop to keep your clinic safe:

1. **CONNECT:** ResilAI connects to your existing security tools (like your email provider or backup system).
2. **VERIFY:** It automatically gathers evidence to confirm these tools are working exactly as intended.
3. **UNDERSTAND:** It translates technical data into a clear "Readiness Score" and simple explanations so you know exactly where you stand.
4. **ACT:** If a protection fails, ResilAI provides clear, step-by-step instructions (and sometimes a one-click fix) to resolve the issue.

---

## 3. Connecting Your Security Tools

ResilAI needs to speak with your existing tools to verify your protections. We do this using "Connectors."

For example:
- **Microsoft / Entra:** Helps ResilAI verify who has access to your systems and email.
- **Wazuh:** Helps ResilAI verify whether your clinic's computers are being actively monitored for threats.
- **Veeam:** Helps ResilAI verify whether your ability to recover data from backups is functioning.
- **Splunk:** Helps ResilAI verify whether security activity across the clinic is being recorded and reviewed.

*Connecting these tools takes only a few minutes and requires no special hardware.*

---

## 4. Understanding Your Readiness Score

Your Readiness Score (from 0 to 100) is a direct reflection of your clinic's verified protections.

**How it is calculated:**
The score starts at 100% and decreases when ResilAI finds a security gap or cannot verify a critical protection. 

**The Golden Rule:**
> The score is calculated from verified evidence and deterministic rules. AI does not decide your readiness score. 

If ResilAI cannot find evidence that a protection is working (for example, if a tool is disconnected), it will **not** assume you are safe. Missing evidence will lower your score because we cannot verify your safety.

---

## 5. Explain "Verified"

In ResilAI, words have very specific meanings to ensure you are never misled about your safety:

- **Configured:** Your IT team set up the tool. (ResilAI doesn't just trust this; it checks.)
- **Connected:** The tool is successfully talking to ResilAI.
- **Verified:** ResilAI has collected fresh evidence that the protection is actively working right now.
- **Unable to Verify:** ResilAI cannot see evidence that the protection is working. (This often happens if a tool breaks or is disconnected.)
- **Stale:** ResilAI has evidence, but it is too old to be trusted.

**Important:** Connecting a security tool does not automatically mean the protection has been verified. ResilAI must see the proof.

---

## 6. Understanding Readiness Gaps

A **readiness gap** occurs when ResilAI finds that a critical protection is missing, failing, or cannot be verified.

**Why does it matter?**
A gap means a door is left unlocked. It represents a specific way an attacker could steal patient data or disrupt your business.

**How severe is it?**
ResilAI categorizes gaps so you know what to prioritize. A "Failed" check means a known protection is broken and needs immediate attention. A "Warning" means something is misconfigured and could become a problem soon.

**What should I do?**
Every readiness gap comes with a clear explanation of "What to do next." Often, you simply need to review the issue and approve the recommended action.

**How does ResilAI verify the fix?**
Once you or your IT team apply a fix, ResilAI will automatically check again. The gap will only be marked as resolved once new evidence proves the protection is working again.

---

## 7. Recovery Readiness

If the worst happens—like a ransomware attack or a server failure—your ability to recover is your last line of defense. ResilAI verifies your recovery readiness.

Key concepts in plain English:
- **RTO (Recovery Time Objective):** How quickly you expect to be operational again. (e.g., "We need to be back up in 4 hours.")
- **RPO (Recovery Point Objective):** How much data you can afford to lose. (e.g., "We can only afford to lose the last 1 hour of patient notes.")
- **Backups:** The secure copies of your data.
- **Recovery Testing:** Actually trying to restore a backup to prove it works.

---

## 8. Security Monitoring

Security monitoring is how the organization notices when something unusual or dangerous happens. 

Attackers try to sneak in quietly. Security monitoring tools act like security cameras and motion detectors for your network, watching for signs of a break-in so you can stop it before damage occurs. ResilAI verifies that these "cameras" are turned on and recording.

---

## 9. Connectors

Here is a list of the integrations ResilAI currently supports to verify your clinic:

| Connector | What it does | Why ResilAI uses it |
| :--- | :--- | :--- |
| **Microsoft 365** | Manages employee email, documents, and logins. | To verify who has access to your systems and ensure email protections are active. |
| **Google Workspace** | Manages employee email, documents, and logins. | To verify who has access to your systems and ensure email protections are active. |
| **Okta** | Manages employee logins and passwords. | To verify that multi-factor authentication (MFA) is strictly enforced. |
| **Wazuh** | Monitors computers and networks for threats. | To verify that your computers are protected against malware and actively monitored. |
| **CrowdStrike** | Advanced protection for computers and servers. | To verify that high-end threat protection is active on critical devices. |
| **Qualys** | Scans for known software weaknesses. | To verify that your systems are updated and not vulnerable to known attacks. |
| **Veeam** | Manages data backups. | To verify that your patient data is safely backed up and can be recovered. |
| **Datto** | Manages data backups. | To verify that your patient data is safely backed up and can be recovered. |
| **Splunk** | Collects and analyzes security activity. | To verify that security logs are being actively reviewed for threats. |
| **AWS Security Hub** | Secures cloud infrastructure. | To verify that your cloud-hosted servers are protected. |
| **Azure Security Center** | Secures cloud infrastructure. | To verify that your cloud-hosted servers are protected. |
| **GCP SCC** | Secures cloud infrastructure. | To verify that your cloud-hosted servers are protected. |

---

## 10. Needs Attention Workflow

When you see a gap in the "Needs Attention" section, the workflow is simple:

1. **Readiness Gap:** ResilAI identifies a failing or unverified protection.
2. **Understand:** Read the plain-English explanation of what happened and why it matters to your business.
3. **Remediate:** Follow the recommended action. Some issues can be fixed automatically with a single click inside ResilAI.
4. **Verify:** ResilAI waits for the security tool to send new evidence.
5. **Verified / Unable to Verify:** ResilAI updates your score only after it has mathematically proven the issue is fixed.

*ResilAI does not simply mark something "fixed" because someone clicked a button. We demand proof.*

---

## 11. Reports

ResilAI provides several ways to view your clinic's status:

- **Morning Brief:** A quick daily summary telling you immediately if the clinic is safe to open or if critical issues need attention. Look here first.
- **Readiness Verification:** The detailed breakdown of your score, showing exactly what is verified and what is failing.
- **Evidence:** The technical proof ResilAI collected from your tools.
- **Last verified time:** Exactly when ResilAI last checked a specific protection.

**Executive Tip:** Start your day with the Morning Brief. If your status is "Safe to Open," you can focus on your patients. If the status is "Action Needed" or "Critical Risk," review the specific Readiness Gaps.

---

## 12. Troubleshooting

Sometimes, things stop working. Here is what to do:

### Connector Unavailable
- **What happened?** ResilAI cannot communicate with one of your security tools (e.g., Microsoft).
- **Why did it happen?** A password may have expired, or the tool's service might be temporarily down.
- **What should I do?** Go to the Connectors page and click "Reconnect" to update the credentials.
- **When should I contact support?** If reconnecting fails multiple times.

### Data Stale
- **What happened?** ResilAI has evidence, but it is too old (e.g., a backup report from 4 days ago).
- **Why did it happen?** The security tool stopped sending updates, or a scheduled task failed.
- **What should I do?** Check the underlying tool (like your backup software) to ensure it is running on schedule.
- **When should I contact support?** If the underlying tool says it is working, but ResilAI still reports stale data.

### Verification Unavailable or No Evidence Available
- **What happened?** ResilAI cannot prove a protection is working.
- **Why did it happen?** The protection might be turned off, or the tool isn't configured to report on it.
- **What should I do?** Review the specific missing protection in your security tool and ensure it is enabled.

### Authentication Issue
- **What happened?** A user cannot log into ResilAI.
- **Why did it happen?** Incorrect password, or their account was disabled by an administrator.
- **What should I do?** Have an administrator check the user's status in the Settings page.

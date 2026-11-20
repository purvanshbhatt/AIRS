import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import { SEOHead } from '../components/common/SEOHead';
import { COMPANY_INFO } from '../config/company';

/**
 * Public trust page: /trust/data-access
 *
 * Every statement here is taken from the code. Sources (keep in step when the
 * code changes):
 *   Hosting region        scripts/deploy_cloud_run.sh (REGION), cloudrun_config.json
 *   Credential encryption app/core/security/connector_encryption.py, encryption.py,
 *                         app/services/connector_manager.py (_encrypt_credentials)
 *   Connector reads       app/connectors/*.py (REQUIRED_PERMISSIONS and collectors),
 *                         app/services/discovery/aws_*.py, app/services/vuln_intel/cloud_deployments.py
 *   Removal               app/api/v1/connectors.py (DELETE), app/services/data_erasure.py,
 *                         app/services/organization.py (delete), app/db/durable_mirror.py
 */

const SECTION = 'py-16 sm:py-20 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40';
const EYEBROW = 'text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald';
const H2 = 'text-2xl sm:text-3xl font-semibold tracking-tight text-on-surface [text-wrap:balance]';
const BODY = 'text-sm sm:text-base text-on-surface-variant leading-relaxed';
const CARD = 'p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60';
const TEXT_LINK = 'font-semibold text-on-surface underline underline-offset-2 hover:text-ready-emerald';
const CODE = 'font-mono text-xs text-on-surface bg-surface-container-high border border-outline-variant/60 rounded px-1.5 py-0.5 break-all';

interface ConnectorRow {
  id: string;
  name: string;
  reads: string[];
  accessNote: string;
  permissions: string[];
}

export const CONNECTOR_ROWS: ConnectorRow[] = [
  {
    id: 'microsoft',
    name: 'Microsoft 365 (Intune, Entra ID, Defender)',
    reads: [
      'Managed devices: name, operating system and version, last check-in, whether the device meets your Intune rules, and whether its disk is encrypted.',
      'User accounts: account ID and sign-in name.',
      'Sign-in rules (conditional access policies), to see whether a second sign-in step is required.',
      'Open Defender security alerts: title, severity, status and the device involved.',
    ],
    accessNote: 'Microsoft Graph application permissions:',
    permissions: [
      'DeviceManagementManagedDevices.Read.All',
      'Policy.Read.All',
      'User.Read.All',
      'SecurityAlert.Read.All',
    ],
  },
  {
    id: 'aws',
    name: 'Amazon Web Services',
    reads: [
      'Security Hub findings that are active and new, and whether GuardDuty is switched on.',
      'The IAM credential report: user names, whether each has multi-factor sign-in, the age of passwords and access keys, and last sign-in dates. The report holds no passwords or secret keys.',
      'Lists of servers and databases (EC2 and RDS), and the software inventory that Systems Manager reports for them.',
      'The network layout: networks, subnets, security group rules, gateways and VPN connections.',
      'A list of hosted services, such as Lambda functions, load balancers, CloudFront, API Gateway and S3 bucket names, for Software Watch.',
    ],
    accessNote:
      'A read-only IAM user (or role) with the AWS-managed SecurityAudit policy. The connector checks for these actions:',
    permissions: [
      'sts:GetCallerIdentity',
      'securityhub:GetFindings',
      'securityhub:DescribeHub',
      'securityhub:GetEnabledStandards',
      'guardduty:ListDetectors',
      'ec2:DescribeInstances',
      'rds:DescribeDBInstances',
      'iam:GetAccountSummary',
      'iam:GenerateCredentialReport',
      'iam:GetCredentialReport',
      'ssm:DescribeInstanceInformation',
    ],
  },
  {
    id: 'duo',
    name: 'Cisco Duo',
    reads: [
      'The sign-in log for the last 7 days (up to 100 entries per sync): user name, sign-in method, result, reason, the IP address of the device, and the time.',
    ],
    accessNote: 'A Duo Admin API key. Access needed:',
    permissions: ['admin:read', 'auth_logs:read'],
  },
  {
    id: 'veeam',
    name: 'Veeam Backup & Replication',
    reads: ['The list of backup jobs: name, type, description, the result of the last run and when it ran.'],
    accessNote: 'A Veeam REST API token. Access needed:',
    permissions: ['backup:read', 'jobs:read'],
  },
  {
    id: 'wazuh',
    name: 'Wazuh',
    reads: [
      'Agents: name, status, IP address, operating system, agent version, last check-in and group.',
      'Known vulnerabilities on active agents: CVE number, package name and version, severity and status.',
      'Recent alerts: the rule that fired, its level, and the agent it fired on.',
    ],
    accessNote: 'A Wazuh API user. Access needed:',
    permissions: ['agent:read', 'vulnerability:read', 'alert:read'],
  },
  {
    id: 'splunk',
    name: 'Splunk',
    reads: [
      'The results of four fixed searches over the last 24 hours: sign-in (MFA) logs, endpoint protection logs, a logging health check and notable events. Each search returns at most 50 log lines.',
      'A list of the hosts that send logs to Splunk, with when each was last heard from.',
      'The log lines those searches return are stored as they arrive, so they contain whatever your logs contain.',
    ],
    accessNote: 'A bearer token for your Splunk MCP server. Access needed:',
    permissions: ['mcp:search'],
  },
  {
    id: 'webhook',
    name: 'Custom webhook',
    reads: [
      'Nothing. ResilAI does not call out to your systems through this connector.',
      'It receives only what your own tools push to it, and each push must carry the shared secret you set. The body is stored as sent.',
    ],
    accessNote: 'A shared secret that you choose, sent in the X-Webhook-Secret header. Access needed:',
    permissions: ['webhook:receive'],
  },
];

const NOT_READ = [
  {
    title: 'No mailboxes, calendars or files in Microsoft 365',
    body: 'None of the four Microsoft permissions ResilAI asks for opens a mailbox, a calendar, or files in OneDrive, SharePoint or Teams.',
  },
  {
    title: 'No stored files or database contents in AWS',
    body: 'ResilAI lists S3 buckets and reads whether each one is set up as a website. It makes no call that opens a stored file or queries a database.',
  },
  {
    title: 'No changes to your systems',
    body: 'Every call ResilAI makes to Microsoft 365, AWS, Duo, Veeam, Wazuh and Splunk reads or searches. Apart from signing in, and asking AWS to prepare its own credential report, it sends nothing that changes a setting.',
  },
  {
    title: 'Nothing installed on your computers',
    body: 'Each connection is made from ResilAI to the service over its API. There is no ResilAI software to install on a computer or server.',
  },
];

export default function DataAccessPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface selection:bg-ready-emerald/20 transition-colors duration-300 flex flex-col font-sans">
      <SEOHead
        title="What ResilAI reads, and where it is kept | ResilAI"
        description="The systems ResilAI connects to, exactly what it reads from each, the access it asks for, where the data is stored, and what happens when you remove a connection."
        canonicalUrl="https://resilai.org/trust/data-access"
      />

      <PublicNavbar />

      <main className="flex-1" data-testid="data-access-page">
        {/* Hero */}
        <section className="pt-12 sm:pt-16 pb-16 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40">
          <div className="max-w-3xl mx-auto space-y-6">
            <p className={EYEBROW}>Trust</p>
            <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-on-surface [text-wrap:balance] leading-[1.1]">
              What ResilAI reads, and where it is kept
            </h1>
            <p className="text-lg text-on-surface-variant leading-relaxed [text-wrap:pretty]">
              ResilAI connects to the systems a practice already uses and asks for read access. This page lists what it
              reads from each one, the access it asks for, where that information is stored, and what is erased
              when you remove it.
            </p>
          </div>
        </section>

        {/* Where it is kept */}
        <section className={SECTION} aria-labelledby="where-kept">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="max-w-3xl space-y-3">
              <h2 id="where-kept" className={H2}>
                Where it is kept
              </h2>
              <p className={BODY}>ResilAI runs on Google Cloud, in the United States.</p>
            </div>
            <dl className="grid gap-6 md:grid-cols-3">
              <div className={`${CARD} space-y-2`}>
                <dt className="text-base font-bold text-on-surface">The service</dt>
                <dd className="text-sm text-on-surface-variant leading-relaxed">
                  The ResilAI API runs on Google Cloud Run in the <code className={CODE}>us-central1</code> region.
                </dd>
              </div>
              <div className={`${CARD} space-y-2`}>
                <dt className="text-base font-bold text-on-surface">The database</dt>
                <dd className="text-sm text-on-surface-variant leading-relaxed">
                  Records are stored in Google Firestore, in the multi-region location{' '}
                  <code className={CODE}>nam5</code> (United States).
                </dd>
              </div>
              <div className={`${CARD} space-y-2`}>
                <dt className="text-base font-bold text-on-surface">Connection details</dt>
                <dd className="text-sm text-on-surface-variant leading-relaxed">
                  The keys and passwords you enter to connect a system are encrypted with AES-256-GCM before they are
                  written to the database. The encryption key is held outside the database, and the connections API
                  does not send a stored key or password back.
                </dd>
              </div>
            </dl>
          </div>
        </section>

        {/* What each connection reads */}
        <section className={`${SECTION} bg-surface-container-low/40`} aria-labelledby="what-read">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="max-w-3xl space-y-3">
              <h2 id="what-read" className={H2}>
                What each connection reads
              </h2>
              <p className={BODY}>
                You choose which systems to connect. ResilAI holds no keys to a system you have not connected.
              </p>
            </div>

            <table className="block md:table w-full text-left border-separate border-spacing-0" data-testid="connector-table">
              <caption className="sr-only">Connections, what each one reads, and the access it asks for</caption>
              <thead className="hidden md:table-header-group">
                <tr>
                  <th scope="col" className="w-[22%] pb-3 pr-6 text-xs font-mono font-bold uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/60">
                    Connection
                  </th>
                  <th scope="col" className="w-[45%] pb-3 pr-6 text-xs font-mono font-bold uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/60">
                    What it reads
                  </th>
                  <th scope="col" className="pb-3 text-xs font-mono font-bold uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/60">
                    Access it asks for
                  </th>
                </tr>
              </thead>
              <tbody className="block md:table-row-group space-y-4 md:space-y-0">
                {CONNECTOR_ROWS.map((row) => (
                  <tr
                    key={row.id}
                    data-testid={`connector-row-${row.id}`}
                    className="block md:table-row rounded-2xl md:rounded-none border md:border-0 border-outline-variant/60 bg-surface-container-low md:bg-transparent p-5 md:p-0 space-y-4 md:space-y-0"
                  >
                    <th scope="row" className="block md:table-cell align-top md:py-5 md:pr-6 text-base font-bold text-on-surface md:border-b md:border-outline-variant/60">
                      {row.name}
                    </th>
                    <td className="block md:table-cell align-top md:py-5 md:pr-6 md:border-b md:border-outline-variant/60">
                      <p className="md:hidden mb-1.5 text-xs font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                        What it reads
                      </p>
                      <ul className="space-y-2 text-sm text-on-surface-variant leading-relaxed">
                        {row.reads.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </td>
                    <td className="block md:table-cell align-top md:py-5 md:border-b md:border-outline-variant/60">
                      <p className="md:hidden mb-1.5 text-xs font-mono font-bold uppercase tracking-wider text-on-surface-variant">
                        Access it asks for
                      </p>
                      <p className="text-sm text-on-surface-variant leading-relaxed">{row.accessNote}</p>
                      <ul className="mt-2 flex flex-wrap gap-1.5">
                        {row.permissions.map((permission) => (
                          <li key={permission} className="min-w-0">
                            <code className={CODE}>{permission}</code>
                          </li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="max-w-3xl text-sm text-on-surface-variant leading-relaxed">
              For Microsoft 365 and AWS, the names above are the vendor&apos;s own permission names. For the other
              connections they are ResilAI&apos;s names for the read access it needs; the middle column says what is
              actually read. In AWS, the network map, the software inventory and the list of hosted services use the
              same read-only identity and make only describe, list and get calls.
            </p>
          </div>
        </section>

        {/* What it does not read */}
        <section className={SECTION} aria-labelledby="not-read">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="max-w-3xl space-y-3">
              <h2 id="not-read" className={H2}>
                What it does not read
              </h2>
            </div>
            <ul className="grid gap-6 sm:grid-cols-2">
              {NOT_READ.map((item) => (
                <li key={item.title} className={`${CARD} space-y-2`}>
                  <h3 className="text-base font-bold text-on-surface">{item.title}</h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">{item.body}</p>
                </li>
              ))}
            </ul>
            <div className={`${CARD} max-w-3xl space-y-2`}>
              <h3 className="text-base font-bold text-on-surface">Personal details it does hold</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                What ResilAI reads includes the names of people and devices: sign-in names (often email addresses),
                device names and IP addresses. Splunk search results and webhook pushes are stored as they arrive, so
                they hold whatever your logs or tools put in them. Connect only the sources you are content to share.
              </p>
            </div>
          </div>
        </section>

        {/* Where a language model is used */}
        <section className={SECTION} aria-labelledby="language-model">
          <div className="max-w-3xl mx-auto space-y-4">
            <h2 id="language-model" className={H2}>
              Where a language model is used
            </h2>
            <p className={BODY}>
              Scores, findings and insurance answers come from fixed rules. No language model produces or changes
              them.
            </p>
            <p className={BODY}>
              Some written text is produced by Google's Gemini model, running on Google Cloud: the summary paragraph
              and the 30, 60 and 90 day plan in a report, and plain-language rewordings of a finding. To write that
              text, ResilAI sends the model your organisation's name, its scores, and the title, severity, evidence
              line and recommended fix of the findings being described.
            </p>
            <p className={BODY}>
              Today this is one setting for the whole service. It cannot yet be switched off for a single
              organisation.
            </p>
          </div>
        </section>

        {/* Business associate agreement */}
        <section className={`${SECTION} bg-surface-container-low/40`} aria-labelledby="baa">
          <div className="max-w-3xl mx-auto space-y-4">
            <h2 id="baa" className={H2}>
              Business associate agreement
            </h2>
            <p className={BODY}>We sign a business associate agreement with healthcare customers on request.</p>
            <p className={BODY}>
              <Link to="/contact" className={`${TEXT_LINK} inline-flex items-center gap-1.5`}>
                <span>Ask for a business associate agreement</span>
                <ArrowRight className="w-4 h-4 shrink-0" aria-hidden />
              </Link>
            </p>
          </div>
        </section>

        {/* Removing your data */}
        <section className={SECTION} aria-labelledby="removing">
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="space-y-3">
              <h2 id="removing" className={H2}>
                Removing your data
              </h2>
              <p className={BODY}>
                Removing something erases it. This is exactly what each step removes and what it keeps.
              </p>
            </div>

            <div className={`${CARD} space-y-2`} data-testid="removal-connector">
              <h3 className="text-base font-bold text-on-surface">When you remove a connection</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                The connection record and its stored keys are erased, together with its sync history, the events read
                through it and the evidence records built from them. This cannot be undone. Kept until you delete the
                organisation: reports you already generated, your score history, and the device and software inventory
                built from that system.
              </p>
            </div>

            <div className={`${CARD} space-y-2`} data-testid="removal-organisation">
              <h3 className="text-base font-bold text-on-surface">When you delete an organisation</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Everything that belongs to the organisation is erased: connections and their stored keys, events and
                evidence, inventory, assessments, reports, score history, API keys and outgoing webhooks. What stays is
                a marker holding the organisation's internal identifier and the time of erasure, so that nothing can be
                restored by mistake, and the ordinary server logs of the hosting provider until they expire.
              </p>
            </div>

            <div className={`${CARD} space-y-2`}>
              <h3 className="text-base font-bold text-on-surface">Cutting off access at the source</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                You can also remove access where it was granted: delete the IAM user, the Microsoft app registration or
                the API token you created for ResilAI. A key that no longer works cannot read anything. For any question
                about erasure, write to{' '}
                <a href={`mailto:${COMPANY_INFO.contactEmail}`} className={`${TEXT_LINK} break-all`}>
                  {COMPANY_INFO.contactEmail}
                </a>
                .
              </p>
            </div>
          </div>
        </section>

        {/* Next step */}
        <section className="py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-surface-container-low/40">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            <h2 className={H2}>A question this page does not answer?</h2>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5">
              <Link
                to="/contact"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 font-bold rounded-xl shadow-sm transition-all duration-200 active:scale-[0.98] min-h-[48px] text-sm text-center whitespace-nowrap"
              >
                <span>Ask us</span>
                <ArrowRight className="w-4 h-4 shrink-0" aria-hidden />
              </Link>
              <Link
                to="/insurance-renewal"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-on-surface font-semibold rounded-xl border border-outline-variant/60 bg-surface-container-low hover:bg-surface-container-high transition-all active:scale-[0.98] min-h-[48px] text-sm text-center whitespace-nowrap"
              >
                <span>Insurance renewal offer</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

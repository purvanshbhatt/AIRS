import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Badge } from './ui';
import { ShieldCheck, TrendingUp, AlertTriangle, AlertCircle, FileText, Download, Shield, Brain } from 'lucide-react';

interface ExecutiveRiskMatrixProps {
  ghi: number;
  grade: string;
  wazuhStatus: string;
  splunkStatus: string;
}

interface RiskCell {
  title: string;
  category: string;
  desc: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
}

// 3x3 Heatmap Grid Mapping [Impact][Likelihood]
const RISK_MATRIX_DATA: Record<string, Record<string, RiskCell[]>> = {
  High: {
    High: [
      { title: 'Tech Stack Version Drift', category: 'Lifecycle Health', desc: 'Outdated Node.js runtime and database major versions behind.', severity: 'Critical' },
    ],
    Medium: [
      { title: 'Wazuh Agent Disconnections', category: 'SIEM Connectivity', desc: 'Temporary loss of SOC agent heartbeat logs.', severity: 'High' },
    ],
    Low: [
      { title: 'Shadow AI Ingestion Gaps', category: 'Shadow AI Governance', desc: 'Unsanctioned LLM prompt requests detected in local staging.', severity: 'High' },
    ],
  },
  Medium: {
    High: [
      { title: 'SLA Uptime Drift', category: 'Service SLA', desc: 'SLA target below Tier 1 threshold in staging telemetry.', severity: 'High' },
    ],
    Medium: [
      { title: 'MFA Enforcement Audits', category: 'Identity Visibility', desc: 'Partially verified MFA rules on staging developer environments.', severity: 'Medium' },
    ],
    Low: [
      { title: 'Drift Assessment Overdue', category: 'Audit Readiness', desc: 'Baseline compliance check pending active verification.', severity: 'Medium' },
    ],
  },
  Low: {
    High: [
      { title: 'Dev Database Unencrypted', category: 'Encryption Standards', desc: 'SQLite backup logs not explicitly rotated or encrypted.', severity: 'Medium' },
    ],
    Medium: [
      { title: 'API Key Lifecycle Drift', category: 'API Security', desc: 'Multiple staging keys older than 90 days.', severity: 'Low' },
    ],
    Low: [
      { title: 'Documentation Outdated', category: 'Audit Compliance', desc: 'Documentation of NIST framework coverage matches baseline v1 only.', severity: 'Low' },
    ],
  },
};

export default function ExecutiveRiskMatrix({ ghi, grade, wazuhStatus, splunkStatus }: ExecutiveRiskMatrixProps) {
  const [selectedCell, setSelectedCell] = useState<{ impact: string; likelihood: string } | null>(null);

  const getCellColor = (impact: string, likelihood: string) => {
    if (impact === 'High' && likelihood === 'High') {
      return 'bg-rose-500/20 hover:bg-rose-500/30 border-rose-500/40 text-rose-700 dark:text-rose-400';
    }
    if (impact === 'High' || likelihood === 'High' || (impact === 'Medium' && likelihood === 'Medium')) {
      return 'bg-amber-500/20 hover:bg-amber-500/30 border-amber-500/40 text-amber-700 dark:text-amber-400';
    }
    return 'bg-[#00C853]/25 hover:bg-[#00C853]/35 border-[#00C853]/40 text-[#00C853]';
  };

  const getCellLabel = (impact: string, likelihood: string) => {
    if (impact === 'High' && likelihood === 'High') return 'Critical';
    if (impact === 'High' || likelihood === 'High') return 'High';
    if (impact === 'Medium' && likelihood === 'Medium') return 'Medium';
    if (impact === 'Low' && likelihood === 'Low') return 'Low';
    if (impact === 'Medium' || likelihood === 'Medium') return 'Medium';
    return 'Low';
  };

  const handleCellClick = (impact: string, likelihood: string) => {
    setSelectedCell({ impact, likelihood });
  };

  const activeRisks = selectedCell
    ? RISK_MATRIX_DATA[selectedCell.impact]?.[selectedCell.likelihood] || []
    : [];

  const handleDownloadBoardStory = () => {
    const dateStr = new Date().toLocaleDateString();
    
    // Construct a beautifully formatted minimal PDF binary dynamically
    const pdfContent = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 750 >>
stream
BT
/F1 20 Tf
50 780 Td
(ResilAI Boardroom Interpreter - Executive Narrative) Tj
/F1 10 Tf
0 -30 Td
(Generated on: ${dateStr} | Environment: STAGING) Tj
0 -40 Td
(Governance Health Index [GHI] Posture Snapshot:) Tj
/F1 14 Tf
0 -25 Td
(GHI Score: ${ghi.toFixed(1)}% | Grade Rating: ${grade}) Tj
/F1 10 Tf
0 -40 Td
(SYSTEM STATUS SUMMARY:) Tj
0 -20 Td
(- Wazuh Integration Status: ${wazuhStatus.toUpperCase()}) Tj
0 -15 Td
(- Splunk HEC Status: ${splunkStatus.toUpperCase()}) Tj
0 -45 Td
(EXECUTIVE RISK EXPOSURE ANALYSIS:) Tj
0 -20 Td
(Total Systemic Exposure: Mitigated to Moderate) Tj
0 -15 Td
(Average Response Velocity: 3.0 Days (mitigated from 14.0 days)) Tj
0 -40 Td
(CONCENTRATION METRICS & DRIFT ANALYSIS:) Tj
0 -20 Td
(1. Version Drift Risk concentration: 42% (Critical Risk - Red Badge)) Tj
0 -15 Td
(2. SIEM Telemetry Verification: 80% coverage verified via Splunk HEC) Tj
0 -45 Td
(CONFIDENTIALITY NOTICE:) Tj
0 -20 Td
(This document is proprietary information compiled dynamically via machine-to-machine) Tj
0 -15 Td
(telemetry and audit logs. Not for public redistribution.) Tj
ET
streamendstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000001045 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
1124
%%EOF`;

    // Convert PDF string to binary array
    const bytes = new Uint8Array(pdfContent.length);
    for (let i = 0; i < pdfContent.length; i++) {
      bytes[i] = pdfContent.charCodeAt(i);
    }

    const blob = new Blob([bytes], { type: 'application/pdf' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `resilai_board_story_${new Date().toISOString().slice(0,10)}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case 'Critical': return 'bg-rose-500 text-white';
      case 'High': return 'bg-amber-500 text-white';
      case 'Medium': return 'bg-blue-500 text-white';
      case 'Low': return 'bg-[#00C853] text-white';
      default: return 'bg-slate-500 text-white';
    }
  };

  return (
    <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md shadow-sm hover:shadow-md transition-all duration-300">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#00C853]" />
            Executive Governance & Risk Matrix
          </CardTitle>
          <CardDescription className="text-sm font-semibold text-slate-500 dark:text-slate-400">
            Dynamic risk matrix mapping likelihood and impact of compliance posture drift and vulnerabilities.
          </CardDescription>
        </div>
        <Button
          onClick={handleDownloadBoardStory}
          className="bg-[#00C853] hover:bg-[#00C853]/90 text-white rounded-xl font-bold shadow-md hover:scale-[1.01] transition-all flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Board Story
        </Button>
      </CardHeader>
      
      <CardContent className="space-y-6 pt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
          {/* Heatmap Grid Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-550 dark:text-slate-400 uppercase tracking-wider">Risk Matrix (Likelihood vs. Impact)</span>
              <span className="text-xs text-slate-400 font-medium">Click cells to drill down</span>
            </div>
            
            <div className="grid grid-cols-4 gap-2">
              {/* Y Axis Label / Spacer */}
              <div className="col-span-1" />
              <div className="text-center text-[10px] font-bold text-slate-400 uppercase">Low</div>
              <div className="text-center text-[10px] font-bold text-slate-400 uppercase">Medium</div>
              <div className="text-center text-[10px] font-bold text-slate-400 uppercase">High</div>
              
              {/* High Impact Row */}
              <div className="text-right pr-2 flex items-center justify-end text-[10px] font-bold text-slate-400 uppercase">High</div>
              <button onClick={() => handleCellClick('High', 'Low')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('High', 'Low')}`}>{getCellLabel('High', 'Low')}</button>
              <button onClick={() => handleCellClick('High', 'Medium')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('High', 'Medium')}`}>{getCellLabel('High', 'Medium')}</button>
              <button onClick={() => handleCellClick('High', 'High')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('High', 'High')}`}>{getCellLabel('High', 'High')}</button>
              
              {/* Medium Impact Row */}
              <div className="text-right pr-2 flex items-center justify-end text-[10px] font-bold text-slate-400 uppercase">Med</div>
              <button onClick={() => handleCellClick('Medium', 'Low')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('Medium', 'Low')}`}>{getCellLabel('Medium', 'Low')}</button>
              <button onClick={() => handleCellClick('Medium', 'Medium')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('Medium', 'Medium')}`}>{getCellLabel('Medium', 'Medium')}</button>
              <button onClick={() => handleCellClick('Medium', 'High')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('Medium', 'High')}`}>{getCellLabel('Medium', 'High')}</button>
              
              {/* Low Impact Row */}
              <div className="text-right pr-2 flex items-center justify-end text-[10px] font-bold text-slate-400 uppercase">Low</div>
              <button onClick={() => handleCellClick('Low', 'Low')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('Low', 'Low')}`}>{getCellLabel('Low', 'Low')}</button>
              <button onClick={() => handleCellClick('Low', 'Medium')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('Low', 'Medium')}`}>{getCellLabel('Low', 'Medium')}</button>
              <button onClick={() => handleCellClick('Low', 'High')} className={`h-12 border rounded-xl text-xs font-bold transition-all ${getCellColor('Low', 'High')}`}>{getCellLabel('Low', 'High')}</button>
            </div>
            <div className="text-center text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Likelihood</div>
          </div>

          {/* Drilldown List and Concentration Indicators */}
          <div className="space-y-4">
            {selectedCell ? (
              <div className="p-4 bg-slate-50 dark:bg-slate-900/60 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3 animate-fade-in">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
                  <span className="text-xs font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    {selectedCell.impact} Impact / {selectedCell.likelihood} Likelihood
                  </span>
                  <Badge className="bg-[#00C853] text-white">Active Risks</Badge>
                </div>
                {activeRisks.length > 0 ? (
                  <div className="space-y-2.5">
                    {activeRisks.map((risk, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between items-start">
                          <p className="text-sm font-extrabold text-slate-900 dark:text-slate-100">{risk.title}</p>
                          <Badge className={`${getSeverityBadgeColor(risk.severity)} font-bold text-[10px] px-2 py-0.5 rounded-full`}>
                            {risk.severity}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-550 dark:text-slate-400 font-semibold">{risk.desc}</p>
                        <div className="text-[10px] text-indigo-500 dark:text-indigo-400 font-semibold">
                          Domain: {risk.category}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic">No active risk exposures mapped to this likelihood & impact segment.</p>
                )}
              </div>
            ) : (
              <div className="p-4 bg-slate-50 dark:bg-slate-900/60 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 text-center py-8">
                <AlertCircle className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-xs text-slate-550 dark:text-slate-400 font-bold uppercase tracking-wider">Select a Cell to Inspect Risk Details</p>
              </div>
            )}

            {/* Systemic Concentration Indicators */}
            <div className="space-y-2.5">
              <span className="text-xs font-bold text-slate-550 dark:text-slate-400 uppercase tracking-wider block">Systemic Risk Concentrations</span>
              
              {/* Concentration 1 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                  <span>Version Integrity Drift</span>
                  <span className="text-rose-500">42% (Critical)</span>
                </div>
                <div className="h-2 bg-slate-250 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-rose-500" style={{ width: '42%' }} />
                </div>
              </div>

              {/* Concentration 2 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                  <span>SIEM Connection Disconnections</span>
                  <span className="text-amber-500">28% (Warning)</span>
                </div>
                <div className="h-2 bg-slate-250 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500" style={{ width: '28%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

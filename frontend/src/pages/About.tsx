import { Link } from 'react-router-dom';
import { Shield, BarChart3, Lock, Layers } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { Footer } from '../components/layout/Footer';

export default function About() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-slate-900 font-semibold">
            <Shield className="h-5 w-5 text-primary-600" />
            ResilAI
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/security" className="text-slate-600 hover:text-slate-900">Security</Link>
            <Link to="/pilot" className="text-slate-600 hover:text-slate-900">Pilot Request</Link>
            <Link to="/dashboard" className="text-primary-600 font-medium">Dashboard</Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">About ResilAI</h1>
            <p className="text-slate-600 mt-2">
              Security readiness scoring for executive and engineering decision-making.
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary-600" />
                What ResilAI Measures
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700 space-y-2">
              <p>ResilAI evaluates operational security readiness across telemetry, detection, identity, incident response, and resilience.</p>
              <p>Each assessment produces a weighted readiness score, maturity tier, and prioritized findings mapped to actionable remediation.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-primary-600" />
                Framework Alignment
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700">
              Findings are mapped to MITRE ATT&CK techniques, CIS Controls references, and OWASP risk categories so teams can align internal and external reporting.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Scoring Methodology Overview</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700 space-y-2">
              <p>Scoring is deterministic and rule-based.</p>
              <p>Narrative sections may use LLM generation, but LLM output never modifies numeric readiness scores or severity ranking.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-primary-600" />
                Data Handling and Privacy
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700 space-y-2">
              <p>ResilAI separates local, staging, and production environments to avoid cross-environment data drift.</p>
              <p>Integration credentials are stored as hashes where applicable, and outbound delivery is controlled by scoped API keys and webhook destinations.</p>
            </CardContent>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  );
}


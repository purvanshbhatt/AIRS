import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { Rocket, Send, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button } from '../components/ui';
import { submitPilotRequest, ApiRequestError } from '../api';
import { Footer } from '../components/layout/Footer';

interface PilotFormState {
  company_name: string;
  team_size: string;
  current_security_tools: string;
  email: string;
}

const defaultState: PilotFormState = {
  company_name: '',
  team_size: '',
  current_security_tools: '',
  email: '',
};

export default function PilotPage() {
  const [form, setForm] = useState<PilotFormState>(defaultState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await submitPilotRequest(form);
      setSubmitted(true);
      setForm(defaultState);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to submit pilot request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-slate-900 font-semibold">
            <Rocket className="h-5 w-5 text-primary-600" />
            ResilAI Pilot
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/about" className="text-slate-600 hover:text-slate-900">About</Link>
            <Link to="/security" className="text-slate-600 hover:text-slate-900">Security</Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-2xl mx-auto px-4 py-10">
          <Card>
            <CardHeader>
              <CardTitle>Request a Pilot</CardTitle>
            </CardHeader>
            <CardContent>
              {submitted && (
                <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  Submission received. We will follow up soon.
                </div>
              )}
              {error && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={onSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Company Name</label>
                  <input
                    required
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.company_name}
                    onChange={(e) => setForm((prev) => ({ ...prev, company_name: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Team Size</label>
                  <input
                    required
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.team_size}
                    onChange={(e) => setForm((prev) => ({ ...prev, team_size: e.target.value }))}
                    placeholder="e.g. 51-200"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Current Security Tools</label>
                  <textarea
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm min-h-24"
                    value={form.current_security_tools}
                    onChange={(e) => setForm((prev) => ({ ...prev, current_security_tools: e.target.value }))}
                    placeholder="SIEM, EDR, cloud monitoring stack..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                  <input
                    required
                    type="email"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.email}
                    onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                  />
                </div>

                <Button type="submit" disabled={loading} className="gap-2">
                  <Send className="h-4 w-4" />
                  {loading ? 'Submitting...' : 'Submit Pilot Request'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  );
}


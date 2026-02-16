import { Link } from 'react-router-dom';
import { Lock, ShieldCheck, Server, Link2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { Footer } from '../components/layout/Footer';

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-slate-900 font-semibold">
            <Lock className="h-5 w-5 text-primary-600" />
            ResilAI Security
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/about" className="text-slate-600 hover:text-slate-900">About</Link>
            <Link to="/pilot" className="text-slate-600 hover:text-slate-900">Pilot Request</Link>
            <Link to="/dashboard" className="text-primary-600 font-medium">Dashboard</Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
          <h1 className="text-3xl font-bold text-slate-900">Security</h1>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-primary-600" />
                Data Protection Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700">
              Assessment and integration records are stored in controlled backend data stores with scoped access patterns and tenant-bound ownership checks.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Environment Separation</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700">
              Local development, staging, and production run with separate configuration, URLs, and deployment targets to reduce accidental cross-environment impact.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5 text-primary-600" />
                Cloud Infrastructure
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700">
              ResilAI runs on managed cloud services with health checks, environment-specific services, and explicit deployment controls for staging and production.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5 text-primary-600" />
                Integration Security
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700">
              API keys are stored hashed, webhooks support signed delivery, and audit events track key integration actions for operator visibility.
            </CardContent>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  );
}


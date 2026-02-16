import { Link } from 'react-router-dom';
import { Card, Button } from '../components/ui';
import {
  Shield,
  Search,
  Users,
  FileCheck,
  Database,
  Plus,
  ClipboardList,
} from 'lucide-react';

const domains = [
  {
    name: 'Telemetry & Logging',
    weight: 25,
    icon: Database,
    color: 'bg-blue-500',
  },
  {
    name: 'Detection Coverage',
    weight: 20,
    icon: Search,
    color: 'bg-purple-500',
  },
  {
    name: 'Identity Visibility',
    weight: 20,
    icon: Users,
    color: 'bg-green-500',
  },
  {
    name: 'IR Process',
    weight: 15,
    icon: FileCheck,
    color: 'bg-orange-500',
  },
  {
    name: 'Resilience',
    weight: 20,
    icon: Shield,
    color: 'bg-red-500',
  },
];

const stats = [
  {
    label: 'Total Questions',
    value: '30',
    description: 'Across all domains',
  },
  {
    label: 'Maturity Levels',
    value: '5',
    description: 'From Initial to Optimized',
  },
  {
    label: 'Findings Engine',
    value: '15+',
    description: 'Automated security rules',
  },
];

export default function Home() {
  return (
    <div className="space-y-6">
      {/* Welcome Card */}
      <Card variant="elevated" padding="lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">Welcome to ResilAI</h1>
            <p className="text-gray-600 dark:text-slate-300 max-w-2xl">
              AI Incident Readiness Score helps organizations assess their security posture across
              five key domains. Start by creating an organization or launching a new assessment.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/org/new">
              <Button variant="outline" className="gap-2">
                <Plus className="w-4 h-4" />
                New Organization
              </Button>
            </Link>
            <Link to="/assessment/new">
              <Button className="gap-2">
                <ClipboardList className="w-4 h-4" />
                Start Assessment
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Domain Cards */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">Assessment Domains</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {domains.map((domain) => (
            <Card
              key={domain.name}
              padding="md"
              className="hover:shadow-medium transition-shadow"
            >
              <div
                className={`w-10 h-10 ${domain.color} rounded-lg flex items-center justify-center mb-3`}
              >
                <domain.icon className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-slate-100">{domain.name}</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-slate-100 mt-2">{domain.weight}%</p>
              <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Weight in score</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Quick Stats */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label} padding="md">
              <p className="text-sm font-medium text-gray-500 dark:text-slate-400 mb-2">{stat.label}</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-slate-100">{stat.value}</p>
              <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">{stat.description}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}


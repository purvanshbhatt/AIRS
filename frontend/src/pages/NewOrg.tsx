import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createOrganization, ApiRequestError } from '../api';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent,
  Button,
  Input,
  Select
} from '../components/ui';
import { Building2, ArrowRight } from 'lucide-react';

const industries = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'financial', label: 'Financial Services' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail' },
  { value: 'government', label: 'Government' },
  { value: 'education', label: 'Education' },
  { value: 'other', label: 'Other' },
];

const sizes = [
  { value: '1-50', label: 'Small (1-50 employees)' },
  { value: '51-200', label: 'Medium (51-200 employees)' },
  { value: '201-1000', label: 'Large (201-1000 employees)' },
  { value: '1000+', label: 'Enterprise (1000+ employees)' },
];

export default function NewOrg() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [size, setSize] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Organization name is required');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const org = await createOrganization({ name, industry, size });
      navigate('/assessment/new', { state: { organizationId: org.id, organizationName: org.name } });
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage());
      } else {
        setError(err instanceof Error ? err.message : 'Failed to create organization');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      <Card variant="elevated">
        <CardHeader className="pb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <CardTitle className="text-xl">Create Organization</CardTitle>
              <CardDescription>Add a new organization to assess</CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {error && (
            <div className="mb-6 p-3 bg-danger-50 border border-danger-200 rounded-lg text-danger-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Organization Name"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Enter organization name"
              required
            />

            <Select
              label="Industry"
              value={industry}
              onChange={e => setIndustry(e.target.value)}
              options={industries}
              placeholder="Select industry..."
            />

            <Select
              label="Organization Size"
              value={size}
              onChange={e => setSize(e.target.value)}
              options={sizes}
              placeholder="Select size..."
            />

            <div className="pt-4">
              <Button 
                type="submit" 
                variant="primary" 
                size="lg" 
                loading={loading}
                className="w-full"
              >
                Create & Start Assessment
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

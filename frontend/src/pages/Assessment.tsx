import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getRubric, getAssessmentEdit, updateAssessmentEdit, computeScore, prefetchAssessmentSummary, ApiRequestError } from '../api';
import type { Rubric, Question, AssessmentDetail } from '../types';
import { Card, CardContent, Button, Badge, ApiDiagnosticsPanel } from '../components/ui';
import { CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { clsx } from 'clsx';

interface DomainEntry {
  id: string;
  name: string;
  description: string;
  weight: number;
  questions: Question[];
}

export default function Assessment() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, boolean | number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [errorObject, setErrorObject] = useState<Error | null>(null);
  const [activeDomain, setActiveDomain] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getRubric(), getAssessmentEdit(id!)])
      .then(([r, editContext]) => {
        setRubric(r);
        setAssessment(editContext.assessment);
        // Pre-fill answers from optimized answers_map
        if (editContext.answers_map) {
          const normalized = { ...editContext.answers_map };
          // Normalize legacy boolean values that might come as strings
          Object.keys(normalized).forEach(k => {
            const val = normalized[k];
            if (val === 'yes' || val === 'true') normalized[k] = true;
            if (val === 'no' || val === 'false') normalized[k] = false;
            // Ensure numbers are numbers
            if (typeof val === 'string' && !isNaN(Number(val)) && val !== '' && val !== 'yes' && val !== 'no' && val !== 'true' && val !== 'false') {
              normalized[k] = Number(val);
            }
          });
          setAnswers(normalized);
        }

        const domainIds = Object.keys(r.domains);
        if (domainIds.length > 0) {
          setActiveDomain(domainIds[0]);
        }
      })
      .catch((err) => {
        setErrorObject(err instanceof Error ? err : new Error(String(err)));
        if (err instanceof ApiRequestError) {
          setError(err.toDisplayMessage());
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load assessment');
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleAnswerChange = (questionId: string, value: boolean | number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');

    try {
      const formattedAnswers: Record<string, boolean | number> = { ...answers };

      // Use efficient bulk update endpoint
      await updateAssessmentEdit(id!, formattedAnswers);

      await computeScore(id!);
      
      // Prefetch summary for faster Results page load
      prefetchAssessmentSummary(id!);
      
      navigate('/results/' + id);
    } catch (err) {
      setErrorObject(err instanceof Error ? err : new Error(String(err)));
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage());
      } else {
        setError(err instanceof Error ? err.message : 'Failed to submit assessment');
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Convert rubric domains to array with IDs
  const getDomains = (): DomainEntry[] => {
    if (!rubric) return [];
    return Object.entries(rubric.domains).map(([domainId, domain]) => ({
      id: domainId,
      ...domain,
    }));
  };

  const getProgress = () => {
    const domains = getDomains();
    const totalQuestions = domains.reduce((sum, d) => sum + d.questions.length, 0);
    const answered = Object.keys(answers).length;
    return totalQuestions > 0 ? Math.round((answered / totalQuestions) * 100) : 0;
  };

  const getDomainProgress = (domain: DomainEntry) => {
    const answered = domain.questions.filter((q) => answers[q.id] !== undefined).length;
    return { answered, total: domain.questions.length };
  };

  const renderQuestion = (q: Question) => {
    const value = answers[q.id];

    if (q.type === 'boolean') {
      return (
        <button
          type="button"
          onClick={() => handleAnswerChange(q.id, value !== true)}
          className={clsx(
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            value === true ? 'bg-primary-600' : 'bg-gray-200'
          )}
        >
          <span
            className={clsx(
              'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
              value === true ? 'translate-x-6' : 'translate-x-1'
            )}
          />
        </button>
      );
    }

    // Numeric or percentage
    return (
      <div className="flex items-center gap-2">
        <input
          type="number"
          min="0"
          max={q.type === 'percentage' ? 100 : undefined}
          value={typeof value === 'number' ? value : ''}
          onChange={(e) => handleAnswerChange(q.id, parseFloat(e.target.value) || 0)}
          className="w-24 px-3 py-1.5 rounded border border-gray-300 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {q.type === 'percentage' && <span className="text-gray-500 text-sm">%</span>}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center gap-4">
            <div className="flex items-center gap-3 text-danger-600">
              <AlertCircle className="w-6 h-6" />
              <p className="text-lg">{error}</p>
            </div>
            <Link to="/dashboard">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </Button>
            </Link>
          </div>
          {/* Show API Diagnostics for network/CORS errors */}
          {errorObject && (
            <ApiDiagnosticsPanel error={errorObject} autoRun={true} compact={false} />
          )}
        </CardContent>
      </Card>
    );
  }

  if (!rubric || !assessment) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-gray-600">
          Assessment not found
        </CardContent>
      </Card>
    );
  }

  const domains = getDomains();
  const currentDomain = domains.find((d) => d.id === activeDomain);
  const progress = getProgress();
  const isUpdate = assessment.answers && assessment.answers.length > 0;

  return (
    <div className="space-y-6">
      {/* Progress Header */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-gray-900">{assessment.title}</h1>
                {isUpdate && <Badge variant="warning">Editing</Badge>}
              </div>
              <p className="text-sm text-gray-500">
                {isUpdate ? 'Update answers to re-calculate score' : 'Answer all questions to complete the assessment'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-primary-600">{progress}%</p>
              <p className="text-xs text-gray-500">Complete</p>
            </div>
          </div>
          <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Domain Tabs */}
      <div className="flex flex-wrap gap-2">
        {domains.map((domain) => {
          const domainProgress = getDomainProgress(domain);
          const isComplete = domainProgress.answered === domainProgress.total;
          const isActive = activeDomain === domain.id;

          return (
            <button
              key={domain.id}
              onClick={() => setActiveDomain(domain.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
              )}
            >
              {domain.name}
              <Badge
                variant={isComplete ? 'success' : isActive ? 'default' : 'outline'}
                className={clsx(isActive && !isComplete && 'bg-white/20 text-white')}
              >
                {domainProgress.answered}/{domainProgress.total}
              </Badge>
              {isComplete && <CheckCircle className="w-4 h-4" />}
            </button>
          );
        })}
      </div>

      {/* Questions */}
      {currentDomain && (
        <Card>
          <CardContent className="divide-y divide-gray-100">
            {currentDomain.questions.map((q, idx) => (
              <div key={q.id} className="py-4 first:pt-0 last:pb-0">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">
                      {idx + 1}. {q.text}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {q.points} point{q.points !== 1 ? 's' : ''} • {q.type}
                    </p>
                  </div>
                  {renderQuestion(q)}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Submit */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={() => navigate('/results/' + id)}>
          Cancel
        </Button>
        <div className="flex items-center gap-4">
          <p className="text-sm text-gray-500 text-right">
            {progress < 100
              ? `Complete all questions to submit (${100 - progress}% remaining)`
              : 'All questions answered!'}
          </p>
          <Button
            onClick={handleSubmit}
            disabled={progress < 100 || submitting}
            loading={submitting}
          >
            {submitting ? 'Processing...' : (isUpdate ? 'Save & Re-calculate' : 'Submit Assessment')}
          </Button>
        </div>
      </div>
    </div>
  );
}


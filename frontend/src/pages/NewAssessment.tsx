import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  getOrganizations,
  getRubric,
  createAssessment,
  submitAnswers,
  computeScore,
  ApiRequestError,
} from '../api';
import type { Rubric, Domain } from '../types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  Input,
  Select,
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
  Badge,
  useToast,
} from '../components/ui';
import {
  ClipboardList,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Save,
  CheckCircle,
  Database,
  Search,
  Users,
  FileCheck,
  Shield,
  Loader2,
  RotateCcw,
} from 'lucide-react';

// Domain icons mapping
const domainIcons: Record<string, typeof Database> = {
  telemetry_logging: Database,
  detection_coverage: Search,
  identity_visibility: Users,
  ir_process: FileCheck,
  resilience: Shield,
};

const domainColors: Record<string, string> = {
  telemetry_logging: 'bg-blue-500',
  detection_coverage: 'bg-purple-500',
  identity_visibility: 'bg-green-500',
  ir_process: 'bg-orange-500',
  resilience: 'bg-red-500',
};

// LocalStorage key
const DRAFT_KEY = 'airs_assessment_draft';

interface DraftData {
  orgId: string;
  title: string;
  answers: Record<string, boolean | number>;
  savedAt: string;
}

export default function NewAssessment() {
  const navigate = useNavigate();
  const { addToast } = useToast();

  // Setup state
  const [step, setStep] = useState<'setup' | 'questions'>('setup');
  const [orgs, setOrgs] = useState<Array<{ id: string; name: string }>>([]);
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [orgId, setOrgId] = useState('');
  const [title, setTitle] = useState('Security Readiness Assessment');
  const [answers, setAnswers] = useState<Record<string, boolean | number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [hasDraft, setHasDraft] = useState(false);

  // Load organizations and rubric
  useEffect(() => {
    Promise.all([getOrganizations(), getRubric()])
      .then(([orgsData, rubricData]) => {
        setOrgs(orgsData);
        setRubric(rubricData);

        // Check for saved draft
        const saved = localStorage.getItem(DRAFT_KEY);
        if (saved) {
          try {
            JSON.parse(saved); // Validate JSON
            setHasDraft(true);
          } catch {
            localStorage.removeItem(DRAFT_KEY);
          }
        }
      })
      .catch((err) => {
        if (err instanceof ApiRequestError) {
          setError(err.toDisplayMessage());
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load data');
        }
      })
      .finally(() => setLoading(false));
  }, []);

  // Restore draft
  const restoreDraft = useCallback(() => {
    const saved = localStorage.getItem(DRAFT_KEY);
    if (saved) {
      try {
        const draft: DraftData = JSON.parse(saved);
        setOrgId(draft.orgId);
        setTitle(draft.title);
        setAnswers(draft.answers);
        setStep('questions');
        addToast({
          type: 'success',
          title: 'Draft restored',
          message: `Loaded draft from ${new Date(draft.savedAt).toLocaleString()}`,
        });
      } catch {
        addToast({ type: 'error', title: 'Failed to restore draft' });
      }
    }
  }, [addToast]);

  // Save draft
  const saveDraft = useCallback(() => {
    const draft: DraftData = {
      orgId,
      title,
      answers,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    addToast({
      type: 'success',
      title: 'Draft saved',
      message: 'Your progress has been saved locally',
    });
  }, [orgId, title, answers, addToast]);

  // Clear draft
  const clearDraft = useCallback(() => {
    localStorage.removeItem(DRAFT_KEY);
    setHasDraft(false);
    setAnswers({});
    addToast({ type: 'info', title: 'Draft cleared' });
  }, [addToast]);

  // Calculate progress
  const progress = useMemo(() => {
    if (!rubric) return { answered: 0, total: 0, percentage: 0 };
    const total = Object.values(rubric.domains).reduce(
      (sum, domain) => sum + domain.questions.length,
      0
    );
    const answered = Object.keys(answers).length;
    return {
      answered,
      total,
      percentage: total > 0 ? Math.round((answered / total) * 100) : 0,
    };
  }, [rubric, answers]);

  // Domain progress
  const getDomainProgress = useCallback(
    (domain: Domain) => {
      const answered = domain.questions.filter((q) => answers[q.id] !== undefined).length;
      return { answered, total: domain.questions.length };
    },
    [answers]
  );

  // Handle answer change
  const handleAnswer = useCallback((questionId: string, value: boolean | number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }, []);

  // Submit assessment
  const handleSubmit = async () => {
    if (!orgId || !rubric) return;

    setSubmitting(true);
    setError('');

    try {
      // 1. Create assessment
      const assessment = await createAssessment({ organization_id: orgId, title });

      // 2. Submit answers
      const formattedAnswers: Record<string, string | number | boolean> = {};
      for (const [qId, value] of Object.entries(answers)) {
        formattedAnswers[qId] = value;
      }
      await submitAnswers(assessment.id, formattedAnswers);

      // 3. Compute score
      await computeScore(assessment.id);

      // 4. Clear draft
      localStorage.removeItem(DRAFT_KEY);

      // 5. Navigate to results
      addToast({
        type: 'success',
        title: 'Assessment complete!',
        message: 'Redirecting to results...',
      });

      navigate(`/dashboard/results/${assessment.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage());
      } else {
        setError(err instanceof Error ? err.message : 'Failed to submit assessment');
      }
      setSubmitting(false);
    }
  };

  // Render setup step
  const renderSetup = () => (
    <div className="max-w-xl mx-auto">
      <Card variant="elevated">
        <CardHeader className="pb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <CardTitle className="text-xl">New Assessment</CardTitle>
              <CardDescription>Start a new security readiness assessment</CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {error && (
            <div className="mb-6 p-3 bg-danger-50 border border-danger-200 rounded-lg text-danger-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {hasDraft && (
            <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-primary-900">Draft available</p>
                  <p className="text-sm text-primary-700">You have an unsaved assessment</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={clearDraft}>
                    Discard
                  </Button>
                  <Button size="sm" onClick={restoreDraft}>
                    Restore
                  </Button>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-5">
            <Select
              label="Organization"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              options={orgs.map((org) => ({ value: org.id, label: org.name }))}
              placeholder={loading ? 'Loading...' : 'Select organization...'}
              disabled={loading}
            />

            {!loading && orgs.length === 0 && (
              <p className="text-sm text-gray-500">
                No organizations found.{' '}
                <Link to="/org/new" className="text-primary-600 hover:text-primary-700 font-medium">
                  Create one first
                </Link>
                .
              </p>
            )}

            <Input
              label="Assessment Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter assessment title"
            />
          </div>
        </CardContent>

        <CardFooter className="flex justify-end">
          <Button
            onClick={() => setStep('questions')}
            disabled={!orgId || !rubric}
            className="gap-2"
          >
            Continue to Questions
            <ArrowRight className="w-4 h-4" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );

  // Render questions step
  const renderQuestions = () => {
    if (!rubric) return null;

    const domains = Object.entries(rubric.domains);

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Progress Header */}
        <Card>
          <CardContent className="py-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{title}</h1>
                <p className="text-sm text-gray-500">
                  {orgs.find((o) => o.id === orgId)?.name || 'Organization'}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary-600">{progress.percentage}%</p>
                  <p className="text-xs text-gray-500">
                    {progress.answered} of {progress.total} answered
                  </p>
                </div>
                <div className="w-24 h-24 relative">
                  <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      className="stroke-gray-200"
                      strokeWidth="8"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      className="stroke-primary-500"
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={2 * Math.PI * 40}
                      strokeDashoffset={2 * Math.PI * 40 * (1 - progress.percentage / 100)}
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 transition-all duration-300"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Error message */}
        {error && (
          <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg text-danger-700 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Domain Accordions */}
        <Card>
          <CardContent className="p-0">
            <Accordion defaultOpen={[domains[0]?.[0]]}>
              {domains.map(([domainId, domain]) => {
                const Icon = domainIcons[domainId] || Shield;
                const color = domainColors[domainId] || 'bg-gray-500';
                const domainProgress = getDomainProgress(domain);
                const isComplete = domainProgress.answered === domainProgress.total;

                return (
                  <AccordionItem key={domainId} id={domainId}>
                    <AccordionTrigger>
                      <div className="flex items-center justify-between w-full pr-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center`}
                          >
                            <Icon className="w-4 h-4 text-white" />
                          </div>
                          <div className="text-left">
                            <p className="font-medium text-gray-900">{domain.name}</p>
                            <p className="text-xs text-gray-500">{domain.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={isComplete ? 'success' : 'default'}
                            className="text-xs"
                          >
                            {domainProgress.answered}/{domainProgress.total}
                          </Badge>
                          {isComplete && <CheckCircle className="w-4 h-4 text-success-500" />}
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-4 pt-2">
                        {domain.questions.map((question, idx) => (
                          <div
                            key={question.id}
                            className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-gray-50 rounded-lg"
                          >
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                {idx + 1}. {question.text}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                {question.points} point{question.points !== 1 ? 's' : ''} •{' '}
                                {question.type}
                              </p>
                            </div>

                            {question.type === 'boolean' ? (
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => handleAnswer(question.id, false)}
                                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    answers[question.id] === false
                                      ? 'bg-danger-100 text-danger-700 ring-2 ring-danger-500'
                                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                                  }`}
                                >
                                  No
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleAnswer(question.id, true)}
                                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    answers[question.id] === true
                                      ? 'bg-success-100 text-success-700 ring-2 ring-success-500'
                                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                                  }`}
                                >
                                  Yes
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2">
                                <input
                                  type="number"
                                  min="0"
                                  max={question.type === 'percentage' ? 100 : undefined}
                                  value={typeof answers[question.id] === 'number' ? (answers[question.id] as number) : ''}
                                  onChange={(e) =>
                                    handleAnswer(question.id, parseFloat(e.target.value) || 0)
                                  }
                                  placeholder={question.type === 'percentage' ? '0-100' : 'Enter value'}
                                  className="w-28 px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                />
                                {question.type === 'percentage' && (
                                  <span className="text-gray-500 text-sm">%</span>
                                )}
                                {question.type === 'numeric' && question.id.includes('retention') && (
                                  <span className="text-gray-500 text-sm">days</span>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => setStep('setup')} className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <Button variant="outline" onClick={clearDraft} className="gap-2">
              <RotateCcw className="w-4 h-4" />
              Reset
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={saveDraft} className="gap-2">
              <Save className="w-4 h-4" />
              Save Draft
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={progress.percentage < 100 || submitting}
              loading={submitting}
              className="gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  Submit Assessment
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </div>
        </div>

        {progress.percentage < 100 && (
          <p className="text-center text-sm text-gray-500">
            Complete all {progress.total - progress.answered} remaining questions to submit
          </p>
        )}
      </div>
    );
  };

  // Loading state
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

  return step === 'setup' ? renderSetup() : renderQuestions();
}

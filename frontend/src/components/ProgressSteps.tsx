import { useEffect, useState } from 'react'
import { Shield, BarChart3, FileText, CheckCircle } from 'lucide-react'

interface ProgressStep {
  label: string
  icon: React.ReactNode
}

const STEPS: ProgressStep[] = [
  { label: 'Loading assessment', icon: <Shield className="h-4 w-4" /> },
  { label: 'Computing scores', icon: <BarChart3 className="h-4 w-4" /> },
  { label: 'Mapping findings', icon: <FileText className="h-4 w-4" /> },
  { label: 'Finalizing report', icon: <CheckCircle className="h-4 w-4" /> },
]

/**
 * Multi-step progress indicator that auto-advances through steps.
 * Used during assessment loading / report generation.
 */
export default function ProgressSteps() {
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    // Auto-advance steps with realistic timing
    const delays = [800, 1200, 1000, 600]
    let timeout: ReturnType<typeof setTimeout>

    const advance = (step: number) => {
      if (step < STEPS.length) {
        timeout = setTimeout(() => {
          setCurrentStep(step)
          advance(step + 1)
        }, delays[step] || 800)
      }
    }
    advance(1)

    return () => clearTimeout(timeout)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <div className="w-full max-w-sm space-y-4">
        {/* Progress bar */}
        <div className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-600 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        {/* Steps */}
        <div className="space-y-2">
          {STEPS.map((step, i) => {
            const isActive = i === currentStep
            const isDone = i < currentStep
            return (
              <div
                key={step.label}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-300 ${
                  isActive
                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : isDone
                    ? 'text-green-600 dark:text-green-400 opacity-70'
                    : 'text-gray-400 dark:text-gray-500 opacity-50'
                }`}
              >
                <span className={isActive ? 'animate-pulse' : ''}>{step.icon}</span>
                <span className="text-sm font-medium">{step.label}</span>
                {isDone && <CheckCircle className="h-3.5 w-3.5 ml-auto text-green-500" />}
                {isActive && (
                  <div className="ml-auto h-3.5 w-3.5 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
                )}
              </div>
            )
          })}
        </div>

        <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-4">
          Analyzing AI security posture…
        </p>
      </div>
    </div>
  )
}

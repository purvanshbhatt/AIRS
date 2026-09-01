import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorBoundaryProps extends React.PropsWithChildren {
  onRetry?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  timestamp: string | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null, timestamp: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error, errorInfo: null, timestamp: new Date().toISOString() };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    console.error('[ErrorBoundary] Uncaught application error:', error, errorInfo);
  }

  handleRetry = () => {
    if (this.props.onRetry) {
      this.setState({ hasError: false, error: null, errorInfo: null, timestamp: null });
      this.props.onRetry();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-surface dark:bg-surface flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-surface-container-low border border-outline-variant rounded-xl p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-critical-red shrink-0" />
              <h1 className="text-xl font-bold text-on-surface">Application Error</h1>
            </div>
            
            <div className="bg-critical-red/10 text-critical-red p-4 rounded-lg mb-6 border border-critical-red/20 font-medium">
              No readiness status has been inferred.
            </div>

            <p className="text-sm text-on-surface-variant mb-6 leading-relaxed">
              The application encountered an unexpected failure condition. Telemetry could not be fully loaded. Please review the diagnostic information below or retry the operation.
            </p>

            <div className="bg-surface-container rounded-lg border border-surface-bright p-4 mb-6 font-mono text-xs overflow-x-auto text-on-surface-variant">
              <div className="mb-2 pb-2 border-b border-surface-bright flex justify-between">
                <span className="font-bold text-on-surface">Diagnostic Information</span>
                <span>{this.state.timestamp}</span>
              </div>
              <div className="text-critical-red font-semibold mb-2">
                {this.state.error?.toString()}
              </div>
              <div className="whitespace-pre-wrap opacity-80">
                {this.state.errorInfo?.componentStack || this.state.error?.stack}
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={this.handleRetry}
                className="inline-flex items-center gap-2 rounded-lg bg-ready-emerald px-5 py-2.5 text-sm font-semibold text-on-primary-container hover:brightness-110 transition-all"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Retry</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}


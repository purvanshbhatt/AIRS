import { useEffect, useState, createContext, useContext, ReactNode } from 'react';
import { clsx } from 'clsx';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';

// Toast types
export interface Toast {
  id: string;
  title?: string;
  message?: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

// Toast Context
interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

// Toast Provider
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

// Toast Container
function ToastContainer() {
  const { toasts } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}

// Toast Item
function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToast();
  const duration = toast.duration ?? 5000;

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => removeToast(toast.id), duration);
      return () => clearTimeout(timer);
    }
  }, [duration, removeToast, toast.id]);

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const styles = {
    success: 'bg-success-50 border-success-500 text-success-600',
    error: 'bg-danger-50 border-danger-500 text-danger-600',
    warning: 'bg-warning-50 border-warning-500 text-warning-600',
    info: 'bg-primary-50 border-primary-500 text-primary-600',
  };

  const Icon = icons[toast.type || 'info'];
  const typeStyle = styles[toast.type || 'info'];

  return (
    <div
      className={clsx(
        'pointer-events-auto bg-white rounded-lg shadow-medium border-l-4 p-4 flex items-start gap-3 animate-in slide-in-from-right-full',
        typeStyle
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        {toast.title && (
          <p className="text-sm font-medium text-gray-900">{toast.title}</p>
        )}
        <p className={clsx('text-sm', toast.title ? 'text-gray-600' : 'text-gray-900')}>
          {toast.message}
        </p>
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        className="flex-shrink-0 text-gray-400 hover:text-gray-500"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export default ToastProvider;

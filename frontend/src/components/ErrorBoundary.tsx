// components/ErrorBoundary.tsx — Catches render crashes and shows a recovery UI

import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen w-screen flex items-center justify-center bg-surface p-8">
          <div className="flex flex-col items-center text-center max-w-md">
            <div className="w-16 h-16 rounded-2xl bg-status-human/10 flex items-center justify-center mb-4">
              <AlertTriangle size={28} className="text-status-human" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">Something went wrong</h2>
            <p className="text-sm text-gray-400 mb-6">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              <RefreshCw size={14} />
              Retry
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

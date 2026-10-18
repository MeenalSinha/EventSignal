import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an unhandled rendering error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-8 text-center my-6 shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600 mb-4">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="font-display text-lg font-bold text-ink">
            {this.props.fallbackTitle || "Unable to display this section"}
          </h3>
          <p className="mt-2 text-sm text-ink-soft max-w-md mx-auto">
            {this.state.error?.message || "An unexpected rendering error occurred while loading demonstration records."}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              onClick={this.handleRetry}
              className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-paper hover:bg-ink-soft transition"
            >
              Retry Section
            </button>
            <button
              onClick={() => window.location.reload()}
              className="rounded-xl border border-line bg-paper px-4 py-2 text-xs font-semibold text-ink hover:bg-paper-warm transition"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

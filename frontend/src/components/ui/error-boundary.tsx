"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "./button";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center p-8 text-center min-h-[200px]">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-cortex-error/15">
            <AlertTriangle className="h-6 w-6 text-cortex-error" />
          </div>
          <h3 className="mb-1 text-sm font-semibold text-cortex-text">Something went wrong</h3>
          <p className="mb-4 text-xs text-cortex-muted max-w-xs">
            {this.state.error?.message ?? "An unexpected error occurred"}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={this.handleReset}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

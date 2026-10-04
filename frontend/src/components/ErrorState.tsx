import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

interface ErrorStateProps {
  message: string;
  code?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ message, code, onRetry, className = "" }: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-6 text-center rounded-lg border border-[var(--danger)]/30 bg-[var(--danger)]/5 ${className}`}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--danger)]/10 text-[var(--danger)] mb-3">
        <AlertCircle className="h-5 w-5" />
      </div>
      <p className="text-sm font-medium text-[var(--text)] mb-1">{message}</p>
      {code && <p className="text-xs font-mono text-[var(--text-muted)] mb-4">{code}</p>}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded bg-white/10 text-[var(--text)] hover:bg-white/15 transition-all cursor-pointer"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Retry
        </button>
      )}
    </div>
  );
}

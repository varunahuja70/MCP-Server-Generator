import React from "react";
import { AlertCircle, CheckCircle, MapPin } from "lucide-react";

export interface ValidationIssue {
  code?: string;
  message: string;
  location?: string;
  hint?: string;
}

interface ValidationReportProps {
  valid: boolean;
  title?: string;
  version?: string;
  format?: string;
  operationCount?: number;
  issues?: ValidationIssue[];
}

export function ValidationReport({
  valid,
  title,
  version,
  format,
  operationCount,
  issues = [],
}: ValidationReportProps) {
  if (valid) {
    return (
      <div className="rounded-lg border border-[#15803D]/40 bg-[#15803D]/10 p-4">
        <div className="flex items-center gap-2.5 text-[#3DD68C] mb-2">
          <CheckCircle className="h-4 w-4" />
          <h4 className="text-sm font-semibold">Valid Specification</h4>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mt-3 pt-3 border-t border-[#15803D]/20 text-[var(--text)]">
          {title && (
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Title</span>
              <span className="font-medium truncate block">{title}</span>
            </div>
          )}
          {version && (
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Version</span>
              <span className="font-mono">{version}</span>
            </div>
          )}
          {format && (
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Format</span>
              <span className="font-mono uppercase">{format}</span>
            </div>
          )}
          {operationCount !== undefined && (
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Operations</span>
              <span className="font-mono font-semibold">{operationCount}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--danger)]/40 bg-[var(--danger)]/10 p-4 space-y-3">
      <div className="flex items-center gap-2 text-[var(--danger)]">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <h4 className="text-sm font-semibold">Specification Validation Errors</h4>
      </div>

      <div className="space-y-2 mt-2">
        {issues.map((iss, idx) => (
          <div
            key={idx}
            className="p-3 rounded bg-black/40 border border-[var(--danger)]/20 text-xs space-y-1"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium text-[var(--text)]">{iss.message}</span>
              {iss.code && (
                <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-white/10 text-[var(--text-muted)] shrink-0">
                  {iss.code}
                </span>
              )}
            </div>

            {iss.location && (
              <div className="flex items-center gap-1.5 text-[var(--text-muted)] font-mono text-[11px]">
                <MapPin className="h-3 w-3 text-[var(--danger)]" />
                <span>{iss.location}</span>
              </div>
            )}

            {iss.hint && (
              <p className="text-[11px] text-[var(--warning)] mt-1">Hint: {iss.hint}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

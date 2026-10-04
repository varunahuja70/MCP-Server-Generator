import React from "react";
import type { SpecDiffReport } from "@/lib/queries";
import { MethodPill } from "./MethodPill";
import { PlusCircle, MinusCircle, RefreshCw } from "lucide-react";

interface SpecDiffViewProps {
  report: SpecDiffReport;
}

export function SpecDiffView({ report }: SpecDiffViewProps) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] bg-[var(--surface-raised)] flex flex-wrap items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-[var(--text)]">
            Changes between Version {report.base_version_no} and Version {report.target_version_no}
          </h4>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Operation differences detected during spec comparison.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1 text-[#3DD68C]">
            <PlusCircle className="h-3.5 w-3.5" />
            <span>+{report.added_count} added</span>
          </span>
          <span className="flex items-center gap-1 text-[var(--danger)]">
            <MinusCircle className="h-3.5 w-3.5" />
            <span>-{report.removed_count} removed</span>
          </span>
          <span className="flex items-center gap-1 text-[var(--warning)]">
            <RefreshCw className="h-3.5 w-3.5" />
            <span>~{report.modified_count} modified</span>
          </span>
        </div>
      </div>

      <div className="divide-y divide-[var(--border)]">
        {!report.operations || report.operations.length === 0 ? (
          <div className="p-6 text-center text-xs text-[var(--text-muted)]">
            No operation additions, deletions, or modifications between these versions.
          </div>
        ) : (
          report.operations.map((op, idx) => {
            const isAdded = op.diff_type === "added";
            const isRemoved = op.diff_type === "removed";

            return (
              <div
                key={idx}
                className="p-3.5 flex items-center justify-between gap-4 hover:bg-white/[0.02]"
              >
                <div className="flex items-center gap-3">
                  <MethodPill method={op.method} />
                  <span className="text-xs font-mono text-[var(--text)]">{op.path}</span>
                  <span className="text-xs text-[var(--text-muted)] font-mono">
                    ({op.operation_key})
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {isAdded && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#15803D]/15 text-[#3DD68C] border border-[#15803D]/30">
                      Added
                    </span>
                  )}
                  {isRemoved && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[var(--danger)]/15 text-[var(--danger)] border border-[var(--danger)]/30">
                      Removed
                    </span>
                  )}
                  {!isAdded && !isRemoved && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[var(--warning)]/15 text-[var(--warning)] border border-[var(--warning)]/30">
                      Modified
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

import React from "react";
import { AlertTriangle } from "lucide-react";

interface ToolBudgetBarProps {
  enabledCount: number;
  recommendedLimit?: number;
  maxLimit?: number;
}

export function ToolBudgetBar({
  enabledCount,
  recommendedLimit = 30,
  maxLimit = 50,
}: ToolBudgetBarProps) {
  const percentage = Math.min(100, Math.round((enabledCount / maxLimit) * 100));
  const isOverRecommended = enabledCount > recommendedLimit;
  const isNearOrOverMax = enabledCount >= maxLimit;

  return (
    <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] space-y-2">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="font-medium text-[var(--text)]">Enabled Tools:</span>
          <span className="font-mono font-bold text-[var(--accent)]">
            {enabledCount}
          </span>
          <span className="text-[var(--text-muted)]">
            / {recommendedLimit} recommended (limit {maxLimit})
          </span>
        </div>

        {isOverRecommended && (
          <div className="flex items-center gap-1 text-[11px] text-[var(--warning)] font-medium">
            <AlertTriangle className="h-3 w-3 shrink-0" />
            <span>High tool count may degrade LLM reasoning performance</span>
          </div>
        )}
      </div>

      <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isNearOrOverMax
              ? "bg-[var(--danger)]"
              : isOverRecommended
              ? "bg-[var(--warning)]"
              : "bg-[#3DD68C]"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

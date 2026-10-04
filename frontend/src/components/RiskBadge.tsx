import React from "react";

interface RiskBadgeProps {
  risk: "read" | "write" | "destructive" | string;
  className?: string;
}

export function RiskBadge({ risk, className = "" }: RiskBadgeProps) {
  const normalized = risk.toLowerCase();

  switch (normalized) {
    case "read":
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-[#15803D]/10 text-[#3DD68C] border-[#15803D]/30 ${className}`}
          title="Safe read-only operation"
        >
          Read
        </span>
      );
    case "write":
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-[#B45309]/10 text-[#F5A524] border-[#B45309]/30 ${className}`}
          title="Mutating state operation"
        >
          Writes
        </span>
      );
    case "destructive":
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-[#DC2626]/10 text-[#F5555D] border-[#DC2626]/30 ${className}`}
          title="Destructive delete or reset operation"
        >
          Deletes
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-white/5 text-[var(--text-muted)] border-[var(--border)] ${className}`}
        >
          {risk}
        </span>
      );
  }
}

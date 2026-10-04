import React from "react";

interface MethodPillProps {
  method: string;
  className?: string;
}

export function MethodPill({ method, className = "" }: MethodPillProps) {
  const m = method.toUpperCase();

  const colorMap: Record<string, string> = {
    GET: "text-[#3DD68C] bg-[#3DD68C]/10 border-[#3DD68C]/30",
    POST: "text-[#7C5CFF] bg-[#7C5CFF]/10 border-[#7C5CFF]/30",
    PUT: "text-[#F5A524] bg-[#F5A524]/10 border-[#F5A524]/30",
    PATCH: "text-[#F5A524] bg-[#F5A524]/10 border-[#F5A524]/30",
    DELETE: "text-[#F5555D] bg-[#F5555D]/10 border-[#F5555D]/30",
    HEAD: "text-[#8A8A93] bg-[#8A8A93]/10 border-[#8A8A93]/30",
    OPTIONS: "text-[#8A8A93] bg-[#8A8A93]/10 border-[#8A8A93]/30",
  };

  const style = colorMap[m] || "text-[var(--text-muted)] bg-white/5 border-[var(--border)]";

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold uppercase tracking-wider border ${style} ${className}`}
    >
      {m}
    </span>
  );
}

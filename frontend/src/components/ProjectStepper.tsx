import React from "react";
import Link from "next/link";
import { Check } from "lucide-react";

export type StepKey = "overview" | "tools" | "settings" | "review" | "builds" | "playground";

interface ProjectStepperProps {
  projectId: string;
  activeStep: StepKey;
}

const STEPS: { key: StepKey; label: string; href: (id: string) => string }[] = [
  { key: "overview", label: "Overview", href: (id) => `/projects/${id}` },
  { key: "tools", label: "Tools", href: (id) => `/projects/${id}/tools` },
  { key: "settings", label: "Settings", href: (id) => `/projects/${id}/settings` },
  { key: "review", label: "Review", href: (id) => `/projects/${id}/review` },
  { key: "builds", label: "Generate", href: (id) => `/projects/${id}/builds` },
  { key: "playground", label: "Test", href: (id) => `/projects/${id}/playground` },
];

export function ProjectStepper({ projectId, activeStep }: ProjectStepperProps) {
  const currentIndex = STEPS.findIndex((s) => s.key === activeStep);

  return (
    <div className="w-full border-b border-[var(--border)] bg-[var(--surface)] py-3 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between sm:justify-start gap-2 sm:gap-6 overflow-x-auto">
        {STEPS.map((s, idx) => {
          const isCurrent = s.key === activeStep;
          const isPassed = idx < currentIndex;

          return (
            <Link
              key={s.key}
              href={s.href(projectId)}
              className={`flex items-center gap-2 text-xs font-medium py-1 px-2.5 rounded-md whitespace-nowrap transition-colors ${
                isCurrent
                  ? "bg-white/10 text-[var(--text)] font-semibold"
                  : isPassed
                  ? "text-[var(--text)] hover:bg-white/5"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
              }`}
            >
              <div
                className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] ${
                  isCurrent
                    ? "bg-[var(--accent)] text-white"
                    : isPassed
                    ? "bg-[#15803D]/20 text-[#3DD68C] border border-[#15803D]/40"
                    : "bg-white/10 text-[var(--text-muted)]"
                }`}
              >
                {isPassed ? <Check className="h-2.5 w-2.5" /> : idx + 1}
              </div>
              <span>{s.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

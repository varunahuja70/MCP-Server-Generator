"use client";

import React, { use } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle,
  ArrowRight,
  RotateCcw,
  Check,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ProjectStepper } from "@/components/ProjectStepper";
import { ErrorState } from "@/components/ErrorState";
import {
  useReviewData,
  useRunReview,
  useAcknowledgeFindings,
} from "@/lib/queries";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ReviewPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const { data: reviewData, isLoading, error, refetch } = useReviewData(projectId);
  const runReviewMutation = useRunReview(projectId);
  const ackMutation = useAcknowledgeFindings(projectId);

  const findings = reviewData?.findings || [];
  const errors = findings.filter((f) => f.severity === "error");
  const warnings = findings.filter((f) => f.severity === "warning");
  const infos = findings.filter((f) => f.severity === "info");

  const unackedErrors = errors.filter((f) => !f.acknowledged);

  const handleAcknowledgeAllErrors = () => {
    const codes = unackedErrors.map((f) => f.code);
    if (codes.length === 0) return;
    ackMutation.mutate(codes);
  };

  const handleAcknowledgeSingle = (code: string) => {
    ackMutation.mutate([code]);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Navbar>
        <div className="space-y-6 max-w-5xl mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">
                Security & Quality Review
              </h1>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Automated vulnerability linting, prompt injection heuristics, and spec quality checks.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => runReviewMutation.mutate()}
                disabled={runReviewMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] transition-all cursor-pointer disabled:opacity-50"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Re-run Review</span>
              </button>

              <Link
                href={`/projects/${projectId}/builds`}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md bg-[var(--accent)] text-white hover:opacity-90 transition-all cursor-pointer shrink-0"
              >
                <span>Proceed to Generate</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          <ProjectStepper projectId={projectId} activeStep="review" />

          {/* Status Alert Banner */}
          {reviewData && (
            <div
              className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                unackedErrors.length > 0
                  ? "border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)]"
                  : "border-[#15803D]/30 bg-[#15803D]/10 text-[#3DD68C]"
              }`}
            >
              <div className="flex items-center gap-3">
                {unackedErrors.length > 0 ? (
                  <ShieldAlert className="h-5 w-5 shrink-0" />
                ) : (
                  <CheckCircle className="h-5 w-5 shrink-0" />
                )}
                <div>
                  <h3 className="text-sm font-semibold">
                    {unackedErrors.length > 0
                      ? `${unackedErrors.length} Blocking Issue(s) Require Acknowledgement`
                      : "Review Passed - Ready for Generation"}
                  </h3>
                  <p className="text-xs opacity-90 mt-0.5">
                    {unackedErrors.length > 0
                      ? "Unacknowledged errors block code generation to protect client and host security."
                      : `${findings.length} total finding(s) discovered across specification.`}
                  </p>
                </div>
              </div>

              {unackedErrors.length > 0 && (
                <button
                  type="button"
                  onClick={handleAcknowledgeAllErrors}
                  disabled={ackMutation.isPending}
                  className="px-3.5 py-1.5 text-xs font-medium rounded bg-[var(--danger)] text-white hover:opacity-90 transition-all cursor-pointer shrink-0"
                >
                  Acknowledge All Errors
                </button>
              )}
            </div>
          )}

          {/* Findings List */}
          {isLoading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-[var(--surface)] rounded-lg" />
              ))}
            </div>
          ) : error ? (
            <ErrorState
              message={error.message || "Failed to load review findings."}
              onRetry={() => refetch()}
            />
          ) : findings.length === 0 ? (
            <div className="p-8 text-center rounded-lg border border-[var(--border)] bg-[var(--surface)]">
              <CheckCircle className="h-8 w-8 text-[#3DD68C] mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-[var(--text)]">No Issues Found</h3>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Your specification complies with all security guidelines and formatting rules.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Errors */}
              {errors.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--danger)] flex items-center gap-1.5">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    <span>Errors ({errors.length})</span>
                  </h3>
                  <div className="space-y-2">
                    {errors.map((f, idx) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-lg border transition-all ${
                          f.acknowledged
                            ? "border-[var(--border)] bg-[var(--surface)] opacity-70"
                            : "border-[var(--danger)]/30 bg-[var(--danger)]/5"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs font-bold text-[var(--text)]">
                                [{f.code}]
                              </span>
                              {f.acknowledged && (
                                <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/10 text-[var(--text-muted)]">
                                  <Check className="h-2.5 w-2.5" /> Acknowledged
                                </span>
                              )}
                            </div>
                            <p className="text-xs font-medium text-[var(--text)]">{f.message}</p>
                            {f.location && (
                              <p className="text-[11px] font-mono text-[var(--text-muted)]">
                                Location: {f.location}
                              </p>
                            )}
                            {f.suggestion && (
                              <p className="text-[11px] text-[var(--warning)] mt-1">
                                Suggestion: {f.suggestion}
                              </p>
                            )}
                          </div>

                          {!f.acknowledged && (
                            <button
                              type="button"
                              onClick={() => handleAcknowledgeSingle(f.code)}
                              className="px-2.5 py-1 text-xs font-medium rounded border border-[var(--border)] hover:bg-white/10 text-[var(--text)] shrink-0 cursor-pointer"
                            >
                              Acknowledge
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Warnings */}
              {warnings.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--warning)] flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span>Warnings ({warnings.length})</span>
                  </h3>
                  <div className="space-y-2">
                    {warnings.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] space-y-1"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-[var(--text)]">
                            [{f.code}]
                          </span>
                        </div>
                        <p className="text-xs font-medium text-[var(--text)]">{f.message}</p>
                        {f.location && (
                          <p className="text-[11px] font-mono text-[var(--text-muted)]">
                            Location: {f.location}
                          </p>
                        )}
                        {f.suggestion && (
                          <p className="text-[11px] text-[var(--warning)] mt-1">
                            Suggestion: {f.suggestion}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Info */}
              {infos.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                    <Info className="h-3.5 w-3.5" />
                    <span>Info ({infos.length})</span>
                  </h3>
                  <div className="space-y-2">
                    {infos.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-xs space-y-1"
                      >
                        <span className="font-mono font-bold text-[var(--text)]">
                          [{f.code}]
                        </span>
                        <p className="text-[var(--text-muted)]">{f.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Navbar>
    </div>
  );
}

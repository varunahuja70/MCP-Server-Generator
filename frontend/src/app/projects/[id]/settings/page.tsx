"use client";

import React, { use, useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight, Check, Save } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ProjectStepper } from "@/components/ProjectStepper";
import { ErrorState } from "@/components/ErrorState";
import {
  useProjectSettings,
  useUpdateProjectSettings,
} from "@/lib/queries";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ProjectSettingsPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const {
    data: settings,
    isLoading: settingsLoading,
    error: settingsError,
    refetch,
  } = useProjectSettings(projectId);

  const updateMutation = useUpdateProjectSettings(projectId);

  const [baseUrl, setBaseUrl] = useState("");
  const [toolPrefix, setToolPrefix] = useState("");
  const [timeoutS, setTimeoutS] = useState(30);
  const [maxRetries, setMaxRetries] = useState(2);
  const [retrySafe, setRetrySafe] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (settings) {
      setBaseUrl(settings.base_url || "");
      setToolPrefix(settings.tool_prefix || "");
      setTimeoutS(settings.timeout_s || 30);
      setMaxRetries(settings.max_retries || 2);
      setRetrySafe(settings.retry_safe_requests ?? true);
    }
  }, [settings]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(false);

    updateMutation.mutate(
      {
        base_url: baseUrl.trim() || null,
        tool_prefix: toolPrefix.trim() || null,
        timeout_s: Number(timeoutS),
        max_retries: Number(maxRetries),
        retry_safe_requests: retrySafe,
      },
      {
        onSuccess: () => {
          setSaveSuccess(true);
          setTimeout(() => setSaveSuccess(false), 3000);
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Navbar>
        <div className="space-y-6 max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">
                Project Settings
              </h1>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Configure runtime timeouts, retries, tool naming prefix, and target API URL.
              </p>
            </div>

            <Link
              href={`/projects/${projectId}/review`}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md bg-[var(--accent)] text-white hover:opacity-90 transition-all cursor-pointer shrink-0"
            >
              <span>Next: Security Review</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <ProjectStepper projectId={projectId} activeStep="settings" />

          {saveSuccess && (
            <div className="p-3 rounded-lg bg-[#15803D]/10 border border-[#15803D]/30 text-xs text-[#3DD68C] flex items-center gap-2">
              <Check className="h-4 w-4" />
              <span>Settings updated successfully.</span>
            </div>
          )}

          {settingsLoading ? (
            <div className="space-y-4 animate-pulse">
              <div className="h-10 bg-[var(--surface)] rounded" />
              <div className="h-28 bg-[var(--surface)] rounded" />
            </div>
          ) : settingsError ? (
            <ErrorState
              message={settingsError.message || "Failed to load project settings."}
              onRetry={() => refetch()}
            />
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="p-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] space-y-4">
                <h3 className="text-sm font-semibold text-[var(--text)] border-b border-[var(--border)] pb-3">
                  API & Runtime Connection
                </h3>

                <div>
                  <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                    Target Base URL
                  </label>
                  <input
                    type="url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="https://api.example.com/v1"
                    className="w-full px-3 py-2 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                  />
                  <p className="text-[11px] text-[var(--text-muted)] mt-1">
                    Default base address for generated HTTP requests. Overrides OpenAPI servers list.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div>
                    <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                      Request Timeout (Seconds)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={300}
                      value={timeoutS}
                      onChange={(e) => setTimeoutS(Number(e.target.value))}
                      className="w-full px-3 py-2 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                      Max Retries for Safe Methods
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={5}
                      value={maxRetries}
                      onChange={(e) => setMaxRetries(Number(e.target.value))}
                      className="w-full px-3 py-2 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                    />
                  </div>
                </div>

                <div className="pt-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="retrySafe"
                    checked={retrySafe}
                    onChange={(e) => setRetrySafe(e.target.checked)}
                    className="h-4 w-4 rounded accent-[var(--accent)] cursor-pointer"
                  />
                  <label htmlFor="retrySafe" className="text-xs text-[var(--text)] cursor-pointer">
                    Enable exponential backoff retries for safe idempotent methods (GET, HEAD, OPTIONS)
                  </label>
                </div>
              </div>

              <div className="p-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] space-y-4">
                <h3 className="text-sm font-semibold text-[var(--text)] border-b border-[var(--border)] pb-3">
                  Naming Conventions & Prefix
                </h3>

                <div>
                  <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                    Tool Prefix (Optional)
                  </label>
                  <input
                    type="text"
                    value={toolPrefix}
                    onChange={(e) => setToolPrefix(e.target.value)}
                    placeholder="e.g. shop (yields shop_list_books)"
                    className="w-full px-3 py-2 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                  />
                  <p className="text-[11px] text-[var(--text-muted)] mt-1">
                    Prepended to all generated MCP tool names to avoid namespace collisions in LLM clients.
                  </p>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-medium rounded bg-[var(--accent)] text-white hover:opacity-90 transition-all cursor-pointer disabled:opacity-50"
                >
                  <Save className="h-3.5 w-3.5" />
                  <span>{updateMutation.isPending ? "Saving..." : "Save Settings"}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </Navbar>
    </div>
  );
}

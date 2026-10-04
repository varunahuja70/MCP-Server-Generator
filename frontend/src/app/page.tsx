"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, BookOpen, ArrowRight, Clock, Sparkles } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { useProjects, useSamples, useCreateSampleProject } from "@/lib/queries";

export default function HomePage() {
  const router = useRouter();
  const { data: projects, isLoading: projectsLoading, error: projectsError, refetch } = useProjects();
  const { data: samples, isLoading: samplesLoading } = useSamples();
  const createSampleMutation = useCreateSampleProject();

  const handleCreateSample = (sampleId: string) => {
    createSampleMutation.mutate(sampleId, {
      onSuccess: (newProj) => {
        router.push(`/projects/${newProj.id}`);
      },
    });
  };

  return (
    <Navbar>
      <div className="space-y-10">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">MCP Forge</h1>
            <p className="text-sm text-[var(--text-muted)] mt-1">
              Generate safe, production-grade MCP server projects from OpenAPI and Swagger specs.
            </p>
          </div>
          <Link
            href="/projects/new"
            className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer shrink-0"
          >
            <Plus className="h-4 w-4" />
            <span>New Project</span>
          </Link>
        </div>

        {/* Try a Sample API Strip */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            <Sparkles className="h-3.5 w-3.5 text-[var(--accent)]" />
            <span>Try a Sample API</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {samplesLoading ? (
              [1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-28 rounded-lg border border-[var(--border)] bg-[var(--surface)] animate-pulse"
                />
              ))
            ) : (
              samples?.map((s) => (
                <div
                  key={s.id}
                  className="group relative flex flex-col justify-between p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--accent)]/50 transition-all"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <h4 className="text-sm font-semibold text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                        {s.title}
                      </h4>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-[var(--text-muted)]">
                        {s.format}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-muted)] line-clamp-2">{s.description}</p>
                  </div>

                  <div className="mt-4 flex items-center justify-between pt-2 border-t border-[var(--border)]/50">
                    <span className="text-[11px] font-mono text-[var(--text-muted)]">
                      {s.operation_count} operations
                    </span>
                    <button
                      type="button"
                      disabled={createSampleMutation.isPending}
                      onClick={() => handleCreateSample(s.id)}
                      className="inline-flex items-center gap-1 text-xs font-medium text-[var(--accent)] hover:underline cursor-pointer disabled:opacity-50"
                    >
                      <span>Create</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Projects List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight text-[var(--text)]">Your Projects</h2>
            {projects && projects.length > 0 && (
              <span className="text-xs font-mono text-[var(--text-muted)]">
                {projects.length} total
              </span>
            )}
          </div>

          {projectsLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="h-20 rounded-lg border border-[var(--border)] bg-[var(--surface)] animate-pulse"
                />
              ))}
            </div>
          ) : projectsError ? (
            <ErrorState
              message={projectsError.message || "Failed to load projects."}
              onRetry={() => refetch()}
            />
          ) : !projects || projects.length === 0 ? (
            <EmptyState
              title="No projects yet"
              description="Import an OpenAPI description or pick one of the bundled samples to generate an MCP server."
              actionText="New Project"
              onAction={() => router.push("/projects/new")}
            />
          ) : (
            <div className="divide-y divide-[var(--border)] rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              {projects.map((p) => (
                <Link
                  key={p.id}
                  href={`/projects/${p.id}`}
                  className="flex items-center justify-between p-4 sm:p-5 hover:bg-white/[0.02] transition-colors block"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--accent)]">
                      <BookOpen className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-[var(--text)] hover:text-[var(--accent)] transition-colors">
                        {p.name}
                      </h3>
                      <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                        {p.slug}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="hidden sm:flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[var(--text-muted)]" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </Navbar>
  );
}

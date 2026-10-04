"use client";

import React, { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileCode,
  Shield,
  Layers,
  Trash2,
  Upload,
  ArrowRight,
  GitCompare,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ProjectStepper } from "@/components/ProjectStepper";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { SpecDiffView } from "@/components/SpecDiffView";
import { ErrorState } from "@/components/ErrorState";
import {
  useProject,
  useSpecVersions,
  useCreateSpecVersion,
  useDeleteProject,
  useSpecDiff,
} from "@/lib/queries";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ProjectOverviewPage({ params }: PageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const { data: project, isLoading: projLoading, error: projError, refetch } = useProject(projectId);
  const { data: specs, isLoading: specsLoading } = useSpecVersions(projectId);
  const createSpecMutation = useCreateSpecVersion(projectId);
  const deleteProjectMutation = useDeleteProject();

  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadContent, setUploadContent] = useState("");
  const [diffBaseVid, setDiffBaseVid] = useState<string>("");
  const [diffTargetVid, setDiffTargetVid] = useState<string>("");

  const { data: diffReport } = useSpecDiff(
    projectId,
    diffBaseVid,
    diffTargetVid
  );

  const latestSpec = specs && specs.length > 0 ? specs[0] : null;

  const handleUploadNewVersion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadContent.trim()) return;

    createSpecMutation.mutate(
      {
        source_type: "paste",
        content: uploadContent.trim(),
      },
      {
        onSuccess: () => {
          setIsUploadOpen(false);
          setUploadContent("");
        },
      }
    );
  };

  const handleDeleteProject = () => {
    if (!project) return;
    deleteProjectMutation.mutate(
      { projectId: project.id, confirmSlug: project.slug },
      {
        onSuccess: () => {
          router.push("/");
        },
      }
    );
  };

  if (projLoading) {
    return (
      <Navbar>
        <div className="space-y-6 animate-pulse max-w-5xl mx-auto">
          <div className="h-10 w-48 bg-white/5 rounded" />
          <div className="h-40 bg-white/5 rounded-lg" />
        </div>
      </Navbar>
    );
  }

  if (projError || !project) {
    return (
      <Navbar>
        <div className="max-w-2xl mx-auto mt-8">
          <ErrorState
            message={projError?.message || "Failed to load project."}
            onRetry={() => refetch()}
          />
        </div>
      </Navbar>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Navbar>
        <div className="space-y-8 max-w-[1440px] mx-auto">
          {/* Top Title & Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">
                  {project.name}
                </h1>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-white/5 text-[var(--text-muted)] border border-[var(--border)]">
                  {project.slug}
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Created on {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setIsUploadOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] transition-all cursor-pointer"
              >
                <Upload className="h-3.5 w-3.5" />
                <span>New Spec Version</span>
              </button>

              <button
                type="button"
                onClick={() => setIsDeleteOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-[var(--danger)]/30 bg-[var(--danger)]/10 text-[var(--danger)] hover:bg-[var(--danger)]/20 transition-all cursor-pointer"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete</span>
              </button>
            </div>
          </div>

          {/* Stepper Navigation */}
          <ProjectStepper projectId={project.id} activeStep="overview" />

          {/* Project Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-1">
                <FileCode className="h-4 w-4 text-[var(--accent)]" />
                <span>Operations</span>
              </div>
              <p className="text-2xl font-bold font-mono text-[var(--text)]">
                {latestSpec ? latestSpec.operation_count : project.operation_count}
              </p>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">
                Detected across endpoints
              </p>
            </div>

            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-1">
                <Layers className="h-4 w-4 text-[#3DD68C]" />
                <span>Spec Format</span>
              </div>
              <p className="text-2xl font-bold font-mono text-[var(--text)] uppercase">
                {latestSpec ? latestSpec.format : "OpenAPI"}
              </p>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">
                {latestSpec?.spec_kind || "Spec 3.x"}
              </p>
            </div>

            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-1">
                <Shield className="h-4 w-4 text-[#F5A524]" />
                <span>Build Status</span>
              </div>
              <p className="text-2xl font-bold font-mono text-[var(--text)] capitalize">
                {project.latest_build_status || "Not built"}
              </p>
              <p className="text-[11px] text-[var(--text-muted)] mt-1">
                Ready to configure and generate
              </p>
            </div>
          </div>

          {/* Spec Version History */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-[var(--text)]">Specification Versions</h2>
              <span className="text-xs text-[var(--text-muted)] font-mono">
                {specs?.length || 0} version(s)
              </span>
            </div>

            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] divide-y divide-[var(--border)]">
              {specsLoading ? (
                <div className="p-4 text-xs text-[var(--text-muted)]">Loading versions...</div>
              ) : !specs || specs.length === 0 ? (
                <div className="p-4 text-xs text-[var(--text-muted)]">No versions imported.</div>
              ) : (
                specs.map((v) => (
                  <div
                    key={v.id}
                    className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-white/[0.01]"
                  >
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-xs font-bold text-[var(--text)]">
                          v{v.version_no}
                        </span>
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 text-[var(--text-muted)] border border-[var(--border)]">
                          {v.spec_kind} ({v.format})
                        </span>
                        {v.source_ref && (
                          <span className="text-xs text-[var(--text-muted)]">
                            {v.source_ref}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)] mt-1 font-mono">
                        <span>SHA: {v.sha256.slice(0, 10)}...</span>
                        <span>{v.operation_count} operations</span>
                        <span>{new Date(v.created_at).toLocaleString()}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {specs.length > 1 && (
                        <button
                          type="button"
                          onClick={() => {
                            // Diff against older or newer version
                            const other = specs.find((s) => s.id !== v.id);
                            if (other) {
                              setDiffBaseVid(other.id);
                              setDiffTargetVid(v.id);
                            }
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)] rounded border border-[var(--border)] hover:bg-white/5 cursor-pointer"
                        >
                          <GitCompare className="h-3 w-3" />
                          <span>Compare Diff</span>
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Diff View if Active */}
          {diffReport && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-[var(--text)]">Version Diff Report</h3>
                <button
                  type="button"
                  onClick={() => {
                    setDiffBaseVid("");
                    setDiffTargetVid("");
                  }}
                  className="text-xs text-[var(--text-muted)] hover:underline cursor-pointer"
                >
                  Close Diff
                </button>
              </div>
              <SpecDiffView report={diffReport} />
            </div>
          )}

          {/* Quick Action Card */}
          <div className="p-6 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-[var(--text)]">
                Ready to configure tools?
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Review operations, customize tool names, and enforce safe defaults.
              </p>
            </div>
            <Link
              href={`/projects/${project.id}/tools`}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md bg-[var(--accent)] text-white hover:opacity-90 transition-all cursor-pointer shrink-0"
            >
              <span>Configure Tools</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </Navbar>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        title={`Delete Project "${project.name}"`}
        description="This will permanently delete this project, all associated spec versions, operation settings, and builds. This action cannot be undone."
        confirmWord={project.slug}
        confirmButtonText="Delete Project"
        isDestructive={true}
        onConfirm={handleDeleteProject}
        onCancel={() => setIsDeleteOpen(false)}
      />

      {/* Upload New Spec Version Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-semibold text-[var(--text)]">
              Upload New Specification Version
            </h3>
            <p className="text-xs text-[var(--text-muted)]">
              Paste the updated OpenAPI/Swagger content. Existing operation choices and renamed tools will be preserved.
            </p>

            <form onSubmit={handleUploadNewVersion} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                  Spec Content
                </label>
                <textarea
                  rows={8}
                  value={uploadContent}
                  onChange={(e) => setUploadContent(e.target.value)}
                  placeholder="Paste OpenAPI YAML or JSON here..."
                  required
                  className="w-full px-3 py-2 text-xs font-mono rounded bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUploadOpen(false)}
                  className="px-3.5 py-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSpecMutation.isPending}
                  className="px-4 py-1.5 text-xs font-medium rounded bg-[var(--accent)] text-white hover:opacity-90 disabled:opacity-50"
                >
                  {createSpecMutation.isPending ? "Ingesting..." : "Ingest Version"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

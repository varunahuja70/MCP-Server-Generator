"use client";

import React, { use, useState, useEffect } from "react";
import Link from "next/link";
import {
  Hammer,
  Download,
  Terminal,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ProjectStepper } from "@/components/ProjectStepper";
import { FileTree } from "@/components/FileTree";
import { CodeViewer } from "@/components/CodeViewer";
import { ConnectPanel } from "@/components/ConnectPanel";
import { ErrorState } from "@/components/ErrorState";
import {
  useProject,
  useProjectBuilds,
  useTriggerBuild,
  useBuildFiles,
  useBuildFileContent,
  useConnectSnippets,
} from "@/lib/queries";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function BuildsPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const { data: project } = useProject(projectId);
  const {
    data: builds,
    isLoading: buildsLoading,
    error: buildsError,
    refetch: refetchBuilds,
  } = useProjectBuilds(projectId);
  const triggerBuildMutation = useTriggerBuild(projectId);

  const [selectedBuildId, setSelectedBuildId] = useState<string>("");
  const [selectedFilePath, setSelectedFilePath] = useState<string>("tools.json");

  // Default to newest build when list arrives
  useEffect(() => {
    if (builds && builds.length > 0 && !selectedBuildId) {
      setSelectedBuildId(builds[0].id);
    }
  }, [builds, selectedBuildId]);

  const activeBuild = builds?.find((b) => b.id === selectedBuildId) || (builds && builds[0]);

  const { data: fileTree } = useBuildFiles(activeBuild ? activeBuild.id : "");
  const { data: fileContent } = useBuildFileContent(
    activeBuild ? activeBuild.id : "",
    selectedFilePath
  );
  const { data: connectSnippets } = useConnectSnippets(activeBuild ? activeBuild.id : "");

  const handleGenerate = () => {
    triggerBuildMutation.mutate(undefined, {
      onSuccess: (newBuild) => {
        setSelectedBuildId(newBuild.id);
        setSelectedFilePath("tools.json");
      },
    });
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Navbar>
        <div className="space-y-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">
                Generate & Builds
              </h1>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Render server projects, inspect source files, download archives, and connect clients.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={triggerBuildMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
              >
                <Hammer className="h-4 w-4" />
                <span>{triggerBuildMutation.isPending ? "Generating..." : "Generate Build"}</span>
              </button>

              <Link
                href={`/projects/${projectId}/playground`}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] transition-all cursor-pointer shrink-0"
              >
                <Terminal className="h-4 w-4 text-[var(--accent)]" />
                <span>Open Playground</span>
              </Link>
            </div>
          </div>

          <ProjectStepper projectId={projectId} activeStep="builds" />

          {/* Builds List & Controls */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--text)]">Build Artifacts</h2>
              <span className="text-xs font-mono text-[var(--text-muted)]">
                {builds?.length || 0} build(s)
              </span>
            </div>

            {buildsLoading ? (
              <div className="h-16 rounded-lg bg-[var(--surface)] animate-pulse" />
            ) : buildsError ? (
              <ErrorState
                message={buildsError.message || "Failed to load builds."}
                onRetry={() => refetchBuilds()}
              />
            ) : !builds || builds.length === 0 ? (
              <div className="p-8 text-center rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface)] space-y-3">
                <Hammer className="h-8 w-8 text-[var(--text-muted)] mx-auto" />
                <h3 className="text-sm font-medium text-[var(--text)]">No builds generated yet</h3>
                <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto">
                  Click &ldquo;Generate Build&rdquo; above to run the review, AST scanner, and package the MCP server project.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {builds.map((b) => {
                  const isSelected = activeBuild?.id === b.id;
                  const isSucceeded = b.status === "succeeded";

                  return (
                    <div
                      key={b.id}
                      onClick={() => setSelectedBuildId(b.id)}
                      className={`p-4 rounded-lg border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                        isSelected
                          ? "border-[var(--accent)] bg-[var(--surface-raised)]"
                          : "border-[var(--border)] bg-[var(--surface)] hover:border-white/20"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${
                            isSucceeded
                              ? "bg-[#15803D]/15 text-[#3DD68C]"
                              : "bg-[var(--danger)]/15 text-[var(--danger)]"
                          }`}
                        >
                          {isSucceeded ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <AlertTriangle className="h-4 w-4" />
                          )}
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-[var(--text)]">
                              Build #{b.build_no}
                            </span>
                            <span
                              className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded ${
                                isSucceeded
                                  ? "bg-[#15803D]/20 text-[#3DD68C]"
                                  : "bg-[var(--danger)]/20 text-[var(--danger)]"
                              }`}
                            >
                              {b.status}
                            </span>
                          </div>

                          <div className="flex items-center gap-4 text-xs font-mono text-[var(--text-muted)] mt-1">
                            <span>{b.tool_count} tools</span>
                            {b.artifact_sha256 && (
                              <span>SHA256: {b.artifact_sha256.slice(0, 12)}...</span>
                            )}
                            <span>{new Date(b.created_at).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>

                      {isSucceeded && (
                        <div className="flex items-center gap-3">
                          <a
                            href={`/api/builds/${b.id}/download`}
                            download
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] transition-all cursor-pointer"
                          >
                            <Download className="h-3.5 w-3.5" />
                            <span>Download ZIP</span>
                          </a>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Active Build Details: File Explorer & Connect */}
          {activeBuild && activeBuild.status === "succeeded" && (
            <div className="space-y-6 pt-4">
              {/* File Browser Grid */}
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-[var(--text)]">Project File Tree</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
                  {/* File tree sidebar */}
                  <div className="p-4 border-r border-[var(--border)] overflow-y-auto max-h-[500px]">
                    {fileTree && fileTree.length > 0 ? (
                      <FileTree
                        items={fileTree}
                        selectedPath={selectedFilePath}
                        onSelectFile={(path) => setSelectedFilePath(path)}
                      />
                    ) : (
                      <div className="text-xs text-[var(--text-muted)] p-2">Loading files...</div>
                    )}
                  </div>

                  {/* Code Viewer Panel */}
                  <div className="md:col-span-2 p-4 overflow-hidden">
                    <CodeViewer
                      code={fileContent?.content || "// Select a file to inspect content."}
                      language={
                        selectedFilePath.endsWith(".json")
                          ? "json"
                          : selectedFilePath.endsWith(".py")
                          ? "python"
                          : selectedFilePath.endsWith(".toml")
                          ? "toml"
                          : selectedFilePath.endsWith(".md")
                          ? "markdown"
                          : "text"
                      }
                      filename={selectedFilePath}
                    />
                  </div>
                </div>
              </div>

              {/* Ready-to-use Client Connect Panel */}
              {connectSnippets && (
                <ConnectPanel
                  snippets={connectSnippets}
                  projectSlug={project?.slug || "mcp-server"}
                />
              )}
            </div>
          )}
        </div>
      </Navbar>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Link as LinkIcon, Sparkles, AlertCircle } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ValidationReport, ValidationIssue } from "@/components/ValidationReport";
import { useCreateProject, useSamples, useCreateSampleProject } from "@/lib/queries";

export default function NewProjectPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"upload" | "paste" | "link" | "samples">("upload");
  const [projectName, setProjectName] = useState("");
  const [specContent, setSpecContent] = useState("");
  const [specUrl, setSpecUrl] = useState("");
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);
  const [generalError, setGeneralError] = useState("");

  const { data: samples, isLoading: samplesLoading } = useSamples();
  const createSampleMutation = useCreateSampleProject();
  const createProjectMutation = useCreateProject();

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    if (!projectName) {
      setProjectName(file.name.replace(/\.(json|yaml|yml)$/i, ""));
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setSpecContent(event.target?.result as string);
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError("");
    setValidationIssues([]);

    if (!projectName.trim()) {
      setGeneralError("Project name is required.");
      return;
    }

    setLoading(true);
    try {
      // 1. Create project
      const newProj = await createProjectMutation.mutateAsync({
        name: projectName.trim(),
      });

      // 2. Ingest specification
      const specPayload: {
        source_type: "upload" | "paste" | "link";
        content?: string;
        url?: string;
        filename?: string;
      } = {
        source_type: activeTab === "link" ? "link" : activeTab === "upload" ? "upload" : "paste",
        content: activeTab === "link" ? undefined : specContent,
        url: activeTab === "link" ? specUrl.trim() : undefined,
        filename: activeTab === "upload" ? fileName : undefined,
      };

      const res = await fetch(`/api/projects/${newProj.id}/specs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Forge-Request": "1",
        },
        body: JSON.stringify(specPayload),
      });

      if (!res.ok) {
        const errJson = await res.json();
        const errPayload = errJson.error || errJson;

        // Populate validation report issues if available
        if (errPayload.details?.issues) {
          setValidationIssues(errPayload.details.issues);
        } else if (errPayload.message) {
          setValidationIssues([
            {
              code: errPayload.code,
              message: errPayload.message,
              hint: errPayload.hint,
              location: errPayload.field || errPayload.location,
            },
          ]);
        }
        setGeneralError(errPayload.message || "Failed to validate and ingest specification.");
        setLoading(false);
        return;
      }

      router.push(`/projects/${newProj.id}`);
    } catch (err: unknown) {
      const e = err as Error;
      setGeneralError(e.message || "An unexpected error occurred during project creation.");
      setLoading(false);
    }
  };

  const handlePickSample = (sampleId: string) => {
    createSampleMutation.mutate(sampleId, {
      onSuccess: (proj) => {
        router.push(`/projects/${proj.id}`);
      },
      onError: (err: Error) => {
        setGeneralError(err.message || "Failed to create sample project.");
      },
    });
  };

  return (
    <Navbar>
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">New MCP Project</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Import an OpenAPI or Swagger 2.0 specification to generate a typed MCP server.
          </p>
        </div>

        {generalError && (
          <div className="p-4 rounded-lg bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-xs text-[var(--danger)] flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold block mb-0.5">Import Error</span>
              <span>{generalError}</span>
            </div>
          </div>
        )}

        {validationIssues.length > 0 && (
          <ValidationReport valid={false} issues={validationIssues} />
        )}

        {/* Tab Selection */}
        <div className="flex items-center gap-1 border-b border-[var(--border)] pb-px">
          {[
            { id: "upload", label: "Upload File", icon: Upload },
            { id: "paste", label: "Paste Spec", icon: FileText },
            { id: "link", label: "Import Link", icon: LinkIcon },
            { id: "samples", label: "Bundled Samples", icon: Sparkles },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  setActiveTab(tab.id as typeof activeTab);
                  setGeneralError("");
                }}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all cursor-pointer ${
                  isActive
                    ? "border-[var(--accent)] text-[var(--text)] font-semibold"
                    : "border-transparent text-[var(--text-muted)] hover:text-[var(--text)]"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {activeTab === "samples" ? (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-[var(--text)]">Select a bundled sample API:</h3>
            <div className="grid grid-cols-1 gap-3">
              {samplesLoading ? (
                <div className="h-32 rounded-lg bg-[var(--surface)] animate-pulse" />
              ) : (
                samples?.map((s) => (
                  <div
                    key={s.id}
                    className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] flex items-center justify-between gap-4 hover:border-[var(--accent)]/50 transition-all"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-semibold text-[var(--text)]">{s.title}</h4>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-[var(--text-muted)]">
                          {s.format}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-muted)]">{s.description}</p>
                    </div>

                    <button
                      type="button"
                      disabled={createSampleMutation.isPending}
                      onClick={() => handlePickSample(s.id)}
                      className="px-3.5 py-1.5 text-xs font-medium rounded-md bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer shrink-0 disabled:opacity-50"
                    >
                      {createSampleMutation.isPending ? "Creating..." : "Use Sample"}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="projectName"
                className="block text-xs font-medium text-[var(--text-muted)] mb-1.5"
              >
                Project Name
              </label>
              <input
                id="projectName"
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Bookshop API"
                required
                className="w-full px-3.5 py-2 text-sm rounded-md bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>

            {activeTab === "upload" && (
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                  Specification File (.json or .yaml)
                </label>
                <div className="border border-dashed border-[var(--border)] rounded-lg p-6 sm:p-8 flex flex-col items-center justify-center text-center bg-[var(--surface)]">
                  <Upload className="h-8 w-8 text-[var(--text-muted)] mb-3" />
                  <p className="text-xs text-[var(--text)] font-medium mb-1">
                    {fileName ? fileName : "Drag and drop or browse OpenAPI spec file"}
                  </p>
                  <p className="text-[11px] text-[var(--text-muted)] mb-4">
                    Supports OpenAPI 3.0, 3.1, 3.2 and Swagger 2.0 (Max 10MB)
                  </p>
                  <input
                    type="file"
                    accept=".json,.yaml,.yml"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="px-3.5 py-1.5 text-xs font-medium rounded bg-white/10 text-[var(--text)] hover:bg-white/15 cursor-pointer transition-all"
                  >
                    Select File
                  </label>
                </div>
              </div>
            )}

            {activeTab === "paste" && (
              <div>
                <label
                  htmlFor="specText"
                  className="block text-xs font-medium text-[var(--text-muted)] mb-1.5"
                >
                  Specification Content (JSON or YAML)
                </label>
                <textarea
                  id="specText"
                  rows={12}
                  value={specContent}
                  onChange={(e) => setSpecContent(e.target.value)}
                  placeholder="Paste OpenAPI YAML or JSON description here..."
                  required
                  className="w-full px-3.5 py-2.5 text-xs font-mono rounded-md bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                />
              </div>
            )}

            {activeTab === "link" && (
              <div>
                <label
                  htmlFor="specUrl"
                  className="block text-xs font-medium text-[var(--text-muted)] mb-1.5"
                >
                  Public OpenAPI URL
                </label>
                <input
                  id="specUrl"
                  type="url"
                  value={specUrl}
                  onChange={(e) => setSpecUrl(e.target.value)}
                  placeholder="https://petstore.swagger.io/v2/swagger.json"
                  required
                  className="w-full px-3.5 py-2 text-sm rounded-md bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                />
                <p className="text-[11px] text-[var(--text-muted)] mt-1.5">
                  Forge fetches the URL with strict SSRF protection (private/loopback addresses blocked).
                </p>
              </div>
            )}

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto px-6 py-2 rounded-md bg-[var(--accent)] text-white text-sm font-medium hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
              >
                {loading ? "Validating & Creating..." : "Create Project"}
              </button>
            </div>
          </form>
        )}
      </div>
    </Navbar>
  );
}

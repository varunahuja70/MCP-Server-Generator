"use client";

import React, { use, useState, useMemo } from "react";
import Link from "next/link";
import { Search, Edit3, ArrowRight } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ProjectStepper } from "@/components/ProjectStepper";
import { MethodPill } from "@/components/MethodPill";
import { RiskBadge } from "@/components/RiskBadge";
import { ToolBudgetBar } from "@/components/ToolBudgetBar";
import { DescriptionEditor } from "@/components/DescriptionEditor";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { ErrorState } from "@/components/ErrorState";
import {
  useOperations,
  useBulkUpdateOperations,
  useApplyOperationsPreset,
  OperationItem,
} from "@/lib/queries";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ToolsConfigPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const {
    data: opsData,
    isLoading: opsLoading,
    error: opsError,
    refetch,
  } = useOperations(projectId);

  const bulkUpdateMutation = useBulkUpdateOperations(projectId);
  const applyPresetMutation = useApplyOperationsPreset(projectId);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRisk, setSelectedRisk] = useState<string>("all");
  const [selectedMethod, setSelectedMethod] = useState<string>("all");

  // Editing tool name inline
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [tempName, setTempName] = useState("");

  // Description drawer
  const [editingDescOp, setEditingDescOp] = useState<OperationItem | null>(null);

  // Write operation enablement confirmation dialog
  const [pendingWriteOp, setPendingWriteOp] = useState<OperationItem | null>(null);

  const operations = opsData?.operations || [];

  const filteredOps = useMemo(() => {
    return operations.filter((op) => {
      if (selectedRisk !== "all" && op.risk !== selectedRisk) return false;
      if (selectedMethod !== "all" && op.method.toUpperCase() !== selectedMethod) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = op.tool_name.toLowerCase().includes(q);
        const matchesPath = op.path.toLowerCase().includes(q);
        const matchesSummary = op.summary?.toLowerCase().includes(q);
        if (!matchesName && !matchesPath && !matchesSummary) return false;
      }
      return true;
    });
  }, [operations, selectedRisk, selectedMethod, searchQuery]);

  const handleToggleOperation = (op: OperationItem) => {
    const willEnable = !op.enabled;

    // Safety check: if enabling a write or destructive operation, require confirmation
    if (willEnable && (op.risk === "write" || op.risk === "destructive")) {
      setPendingWriteOp(op);
      return;
    }

    bulkUpdateMutation.mutate([
      {
        operation_key: op.operation_key,
        enabled: willEnable,
      },
    ]);
  };

  const confirmEnableWrite = () => {
    if (!pendingWriteOp) return;
    bulkUpdateMutation.mutate([
      {
        operation_key: pendingWriteOp.operation_key,
        enabled: true,
      },
    ]);
    setPendingWriteOp(null);
  };

  const handleSaveName = (op: OperationItem) => {
    const trimmed = tempName.trim();
    if (!trimmed || trimmed === op.tool_name) {
      setEditingKey(null);
      return;
    }
    bulkUpdateMutation.mutate([
      {
        operation_key: op.operation_key,
        tool_name_override: trimmed,
      },
    ]);
    setEditingKey(null);
  };

  const handleSaveDescription = (newDesc: string) => {
    if (!editingDescOp) return;
    bulkUpdateMutation.mutate([
      {
        operation_key: editingDescOp.operation_key,
        description_override: newDesc,
      },
    ]);
    setEditingDescOp(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Navbar>
        <div className="space-y-6 max-w-[1440px] mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">
                Tools Configuration
              </h1>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Customize tool names, descriptions, and enable safe operations for AI agents.
              </p>
            </div>

            <Link
              href={`/projects/${projectId}/settings`}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md bg-[var(--accent)] text-white hover:opacity-90 transition-all cursor-pointer shrink-0"
            >
              <span>Next: Project Settings</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <ProjectStepper projectId={projectId} activeStep="tools" />

          {/* Tool Budget Guidance Bar */}
          <ToolBudgetBar
            enabledCount={opsData?.enabled_count || 0}
            recommendedLimit={30}
            maxLimit={50}
          />

          {/* Controls: Presets & Filters */}
          <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              {/* Presets */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-[var(--text-muted)]">Presets:</span>
                <button
                  type="button"
                  onClick={() => applyPresetMutation.mutate({ preset: "read-only" })}
                  className="px-2.5 py-1 text-xs font-medium rounded border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] cursor-pointer"
                >
                  Safe Read-Only
                </button>
                <button
                  type="button"
                  onClick={() => applyPresetMutation.mutate({ preset: "none" })}
                  className="px-2.5 py-1 text-xs font-medium rounded border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] cursor-pointer"
                >
                  Disable All
                </button>
                <button
                  type="button"
                  onClick={() => applyPresetMutation.mutate({ preset: "all" })}
                  className="px-2.5 py-1 text-xs font-medium rounded border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] cursor-pointer"
                >
                  Enable All
                </button>
              </div>

              {/* Counts */}
              <div className="flex items-center gap-4 text-xs font-mono text-[var(--text-muted)]">
                <span>{opsData?.read_count || 0} read</span>
                <span>{opsData?.write_count || 0} write</span>
                <span>{opsData?.destructive_count || 0} destructive</span>
              </div>
            </div>

            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row items-center gap-3 pt-3 border-t border-[var(--border)]">
              <div className="relative flex-1 w-full">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter by tool name, path, or summary..."
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                />
                <Search className="absolute left-3 top-2 h-3.5 w-3.5 text-[var(--text-muted)]" />
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <select
                  value={selectedRisk}
                  onChange={(e) => setSelectedRisk(e.target.value)}
                  className="px-2.5 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none"
                >
                  <option value="all">All Risks</option>
                  <option value="read">Read Only</option>
                  <option value="write">Writes</option>
                  <option value="destructive">Deletes</option>
                </select>

                <select
                  value={selectedMethod}
                  onChange={(e) => setSelectedMethod(e.target.value)}
                  className="px-2.5 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none"
                >
                  <option value="all">All Methods</option>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            </div>
          </div>

          {/* Operations Table */}
          {opsLoading ? (
            <div className="space-y-2 animate-pulse">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-16 rounded bg-[var(--surface)]" />
              ))}
            </div>
          ) : opsError ? (
            <ErrorState
              message={opsError.message || "Failed to load operations."}
              onRetry={() => refetch()}
            />
          ) : (
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--surface-raised)] text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                      <th className="py-2.5 px-4 w-12">On</th>
                      <th className="py-2.5 px-4 w-20">Method</th>
                      <th className="py-2.5 px-4">Endpoint & Path</th>
                      <th className="py-2.5 px-4">MCP Tool Name</th>
                      <th className="py-2.5 px-4 w-24">Risk</th>
                      <th className="py-2.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] text-xs">
                    {filteredOps.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-xs text-[var(--text-muted)]">
                          No operations match your filters.
                        </td>
                      </tr>
                    ) : (
                      filteredOps.map((op) => (
                        <tr
                          key={op.operation_key}
                          className={`hover:bg-white/[0.01] transition-colors ${
                            !op.enabled ? "opacity-60" : ""
                          }`}
                        >
                          {/* Toggle switch */}
                          <td className="py-3 px-4">
                            <input
                              type="checkbox"
                              checked={op.enabled}
                              onChange={() => handleToggleOperation(op)}
                              className="h-4 w-4 rounded accent-[var(--accent)] cursor-pointer"
                            />
                          </td>

                          {/* Method pill */}
                          <td className="py-3 px-4">
                            <MethodPill method={op.method} />
                          </td>

                          {/* Path & summary */}
                          <td className="py-3 px-4">
                            <div className="font-mono text-xs text-[var(--text)] truncate max-w-sm">
                              {op.path}
                            </div>
                            {op.summary && (
                              <div className="text-[11px] text-[var(--text-muted)] truncate max-w-md mt-0.5">
                                {op.summary}
                              </div>
                            )}
                          </td>

                          {/* Tool Name inline editing */}
                          <td className="py-3 px-4">
                            {editingKey === op.operation_key ? (
                              <div className="flex items-center gap-1.5">
                                <input
                                  type="text"
                                  value={tempName}
                                  onChange={(e) => setTempName(e.target.value)}
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") handleSaveName(op);
                                    if (e.key === "Escape") setEditingKey(null);
                                  }}
                                  className="px-2 py-0.5 text-xs font-mono rounded bg-[var(--surface-raised)] border border-[var(--accent)] text-[var(--text)] focus:outline-none"
                                  autoFocus
                                />
                                <button
                                  type="button"
                                  onClick={() => handleSaveName(op)}
                                  className="text-[10px] text-[var(--accent)] hover:underline"
                                >
                                  Save
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 group">
                                <span className="font-mono font-medium text-[var(--text)]">
                                  {op.tool_name}
                                </span>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingKey(op.operation_key);
                                    setTempName(op.tool_name);
                                  }}
                                  className="opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-[var(--text)] transition-opacity cursor-pointer"
                                  title="Rename tool"
                                >
                                  <Edit3 className="h-3 w-3" />
                                </button>
                              </div>
                            )}
                          </td>

                          {/* Risk */}
                          <td className="py-3 px-4">
                            <RiskBadge risk={op.risk} />
                          </td>

                          {/* Actions */}
                          <td className="py-3 px-4 text-right">
                            <button
                              type="button"
                              onClick={() => setEditingDescOp(op)}
                              className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] hover:underline cursor-pointer"
                            >
                              Edit Description
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Navbar>

      {/* Description Editor Drawer */}
      {editingDescOp && (
        <DescriptionEditor
          isOpen={Boolean(editingDescOp)}
          toolName={editingDescOp.tool_name}
          initialDescription={editingDescOp.description || ""}
          onSave={handleSaveDescription}
          onClose={() => setEditingDescOp(null)}
        />
      )}

      {/* Write Operation Confirmation Modal */}
      <ConfirmDialog
        isOpen={Boolean(pendingWriteOp)}
        title={`Enable Mutating Tool "${pendingWriteOp?.tool_name}"`}
        description={`This tool executes a ${pendingWriteOp?.method} request on ${pendingWriteOp?.path} that alters server state. AI agents will be able to perform this action autonomously.`}
        confirmButtonText="Enable Mutating Tool"
        isDestructive={false}
        onConfirm={confirmEnableWrite}
        onCancel={() => setPendingWriteOp(null)}
      />
    </div>
  );
}

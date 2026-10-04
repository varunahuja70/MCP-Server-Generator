"use client";

import React, { use, useState, useEffect } from "react";
import Link from "next/link";
import {
  Play,
  Square,
  Search,
  Radio,
  AlertCircle,
  Hammer,
  ArrowRight,
  Loader2,
  RefreshCw,
  Zap,
  Terminal,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ProjectStepper } from "@/components/ProjectStepper";
import { SchemaForm } from "@/components/SchemaForm";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import {
  useProjectBuilds,
  useCreatePlaygroundSession,
  useDeletePlaygroundSession,
  usePlaygroundTools,
  useCallPlaygroundTool,
  PlaygroundTool,
  ToolCallResult,
  ProtocolTraceMessage,
} from "@/lib/queries";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function PlaygroundPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const { data: builds } = useProjectBuilds(projectId);

  // Playground Session states
  const [targetMode, setTargetMode] = useState<"mock" | "live">("mock");
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [sessionId, setSessionId] = useState<string>("");

  // Tools & Run states
  const [selectedTool, setSelectedTool] = useState<PlaygroundTool | null>(null);
  const [toolSearch, setToolSearch] = useState("");
  const [callResult, setCallResult] = useState<ToolCallResult | null>(null);
  const [pendingRunTool, setPendingRunTool] = useState<{ tool: PlaygroundTool; args: Record<string, unknown> } | null>(
    null
  );

  // Trace messages
  const [traces, setTraces] = useState<ProtocolTraceMessage[]>([]);

  const createSessionMutation = useCreatePlaygroundSession();
  const deleteSessionMutation = useDeletePlaygroundSession();
  const { data: toolsData, isLoading: toolsLoading } = usePlaygroundTools(sessionId);
  const callToolMutation = useCallPlaygroundTool(sessionId);

  // Find most recent succeeded build, or fallback to first build
  const activeBuild =
    builds?.find((b) => b.status === "succeeded") ||
    (builds && builds.length > 0 ? builds[0] : null);

  const [sessionError, setSessionError] = useState<string | null>(null);

  // Real-time SSE Trace streaming
  useEffect(() => {
    if (!sessionId) {
      setTraces([]);
      return;
    }

    const eventSource = new EventSource(`/api/playground/sessions/${sessionId}/trace`);

    eventSource.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setTraces((prev) => [...prev, msg]);
      } catch {
        // Fallback
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  const handleStartSession = () => {
    setSessionError(null);
    if (!activeBuild) {
      setSessionError("No build available. Please generate a server build first.");
      return;
    }

    createSessionMutation.mutate(
      {
        build_id: activeBuild.id,
        target: targetMode,
        env_vars: targetMode === "live" ? credentials : {},
      },
      {
        onSuccess: (session) => {
          const sId = session.session_id || session.id;
          if (sId) {
            setSessionId(sId);
            setCredentials({});
            setSessionError(null);
          } else {
            setSessionError("Received invalid session ID from backend.");
          }
        },
        onError: (err) => {
          setSessionError(err.message || "Failed to start session. Check backend server logs.");
        },
      }
    );
  };

  const handleStopSession = () => {
    if (!sessionId) return;
    deleteSessionMutation.mutate(sessionId, {
      onSuccess: () => {
        setSessionId("");
        setSelectedTool(null);
        setCallResult(null);
        setSessionError(null);
      },
    });
  };

  const handleRunTool = (args: Record<string, unknown>) => {
    if (!selectedTool) return;

    // In live mode, warn before mutating or destructive calls
    const isMutating =
      selectedTool.annotations?.audience !== undefined ||
      selectedTool.name.startsWith("create_") ||
      selectedTool.name.startsWith("delete_") ||
      selectedTool.name.startsWith("update_");

    if (targetMode === "live" && isMutating) {
      setPendingRunTool({ tool: selectedTool, args });
      return;
    }

    executeCall(selectedTool.name, args);
  };

  const executeCall = (toolName: string, args: Record<string, unknown>) => {
    callToolMutation.mutate(
      { name: toolName, arguments: args },
      {
        onSuccess: (res) => {
          setCallResult(res);
        },
        onError: (err: Error) => {
          setCallResult({ error: err.message || "Execution error" });
        },
      }
    );
  };

  const tools = toolsData?.tools || [];
  const filteredTools = tools.filter((t) =>
    toolSearch.trim() ? t.name.toLowerCase().includes(toolSearch.toLowerCase()) : true
  );

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Navbar>
        <div className="space-y-6 max-w-[1440px] mx-auto pb-12">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20 shadow-sm">
                  <Zap className="h-4 w-4" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">Playground</h1>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
                Test generated MCP tools against an in-process mock server or live API with a real-time protocol trace.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {sessionId ? (
                <button
                  type="button"
                  onClick={handleStopSession}
                  disabled={deleteSessionMutation.isPending}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl bg-[var(--danger)]/15 border border-[var(--danger)]/30 text-[var(--danger)] hover:bg-[var(--danger)]/25 active:scale-[0.98] transition-all cursor-pointer shadow-sm"
                >
                  {deleteSessionMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Square className="h-3.5 w-3.5" />
                  )}
                  <span>Stop Session</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleStartSession}
                  disabled={!activeBuild || createSessionMutation.isPending}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold rounded-xl bg-[#26D67C] text-black hover:bg-[#20bd6d] active:scale-[0.98] transition-all cursor-pointer shadow-md shadow-[#26D67C]/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {createSessionMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-black" />
                      <span>Launching Server...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current text-black" />
                      <span>Start Session</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          <ProjectStepper projectId={projectId} activeStep="playground" />

          {/* Warning / Error alerts */}
          {sessionError && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-[var(--danger)]/10 border border-[var(--danger)]/20 text-xs text-[var(--danger)] shadow-sm animate-in fade-in duration-200">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold">Session Error: </span>
                <span>{sessionError}</span>
              </div>
            </div>
          )}

          {!activeBuild && (
            <div className="p-6 rounded-2xl border border-[var(--border)] bg-gradient-to-r from-[var(--surface)] to-[var(--surface-raised)] flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-[var(--accent)]/15 border border-[var(--accent)]/20 flex items-center justify-center text-[var(--accent)] shrink-0">
                  <Hammer className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text)]">No Server Build Found</h3>
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">
                    To start an MCP Playground session, your server code must be generated first.
                  </p>
                </div>
              </div>
              <Link
                href={`/projects/${projectId}/builds`}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] transition-all shrink-0"
              >
                <span>Go to Generate Build</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          )}

          {/* Three-Column Interactive Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Session Controls & Tool List (4 cols) */}
            <div className="lg:col-span-4 space-y-4">
              {/* Session Target Box */}
              <div className="p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                    Session Target
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2.5 w-2.5 rounded-full transition-all duration-300 ${
                        sessionId ? "bg-[#26D67C] ring-4 ring-[#26D67C]/20 animate-pulse" : "bg-white/20"
                      }`}
                    />
                    <span className="text-[11px] font-mono text-[var(--text-muted)]">
                      {sessionId ? "ACTIVE" : "IDLE"}
                    </span>
                  </div>
                </div>

                {!sessionId ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 p-1 bg-[var(--surface-raised)] border border-[var(--border)] rounded-xl text-xs">
                      <button
                        type="button"
                        onClick={() => setTargetMode("mock")}
                        className={`py-2 px-3 rounded-lg font-medium transition-all text-center cursor-pointer ${
                          targetMode === "mock"
                            ? "bg-[var(--accent)] text-white shadow-sm"
                            : "text-[var(--text-muted)] hover:text-[var(--text)]"
                        }`}
                      >
                        Mock Server
                      </button>
                      <button
                        type="button"
                        onClick={() => setTargetMode("live")}
                        className={`py-2 px-3 rounded-lg font-medium transition-all text-center cursor-pointer ${
                          targetMode === "live"
                            ? "bg-[var(--accent)] text-white shadow-sm"
                            : "text-[var(--text-muted)] hover:text-[var(--text)]"
                        }`}
                      >
                        Live Target API
                      </button>
                    </div>

                    {targetMode === "live" ? (
                      <div className="p-3 rounded-xl bg-[var(--warning)]/10 border border-[var(--warning)]/20 text-[11px] text-[var(--warning)] leading-relaxed">
                        Live mode communicates with remote endpoints. Destructive actions will prompt for confirmation.
                      </div>
                    ) : (
                      <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-[11px] text-[var(--text-muted)] leading-relaxed">
                        Mock mode runs entirely in-memory using synthesized mock responses according to your OpenAPI schema.
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs font-mono text-[var(--text-muted)] space-y-2 p-3 rounded-xl bg-[var(--surface-raised)] border border-[var(--border)]">
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-muted)]">Session:</span>
                      <span className="text-[var(--text)] font-semibold">{sessionId.slice(0, 16)}...</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-muted)]">Mode:</span>
                      <span className="capitalize px-1.5 py-0.5 rounded text-[10px] bg-[#26D67C]/15 text-[#26D67C] font-semibold">
                        {targetMode}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Tools List */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                    Tools ({tools.length})
                  </span>
                  {sessionId && toolsLoading && (
                    <RefreshCw className="h-3 w-3 text-[var(--text-muted)] animate-spin" />
                  )}
                </div>

                <div className="relative">
                  <input
                    type="text"
                    value={toolSearch}
                    onChange={(e) => setToolSearch(e.target.value)}
                    placeholder="Search tools..."
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)] transition-colors"
                  />
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[var(--text-muted)]" />
                </div>

                <div className="divide-y divide-[var(--border)] max-h-96 overflow-y-auto rounded-xl border border-[var(--border)] bg-[var(--surface-raised)]">
                  {!sessionId ? (
                    <div className="p-6 text-center text-xs text-[var(--text-muted)] leading-relaxed">
                      Click <strong className="text-[var(--text)]">Start Session</strong> above to start server and view available tools.
                    </div>
                  ) : toolsLoading ? (
                    <div className="p-6 text-center text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-[var(--accent)]" />
                      <span>Listing tools from MCP server...</span>
                    </div>
                  ) : filteredTools.length === 0 ? (
                    <div className="p-6 text-center text-xs text-[var(--text-muted)]">
                      No matching tools found.
                    </div>
                  ) : (
                    filteredTools.map((t) => (
                      <button
                        key={t.name}
                        type="button"
                        onClick={() => {
                          setSelectedTool(t);
                          setCallResult(null);
                        }}
                        className={`w-full py-3 px-3.5 flex flex-col text-left transition-all cursor-pointer ${
                          selectedTool?.name === t.name
                            ? "bg-[var(--accent)]/15 border-l-2 border-[var(--accent)] font-medium text-[var(--text)]"
                            : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
                        }`}
                      >
                        <span className="text-xs font-mono font-medium text-[var(--text)]">{t.name}</span>
                        {t.description && (
                          <span className="text-[11px] text-[var(--text-muted)] truncate max-w-xs mt-0.5">
                            {t.description}
                          </span>
                        )}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Middle Column: Tool Invocation & Results (4 cols) */}
            <div className="lg:col-span-4 space-y-4">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm space-y-4 min-h-[300px]">
                <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                  <h3 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                    {selectedTool ? `Invoke: ${selectedTool.name}` : "Tool Invocation"}
                  </h3>
                  {selectedTool && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-[var(--text-muted)]">
                      schema ready
                    </span>
                  )}
                </div>

                {selectedTool ? (
                  <SchemaForm
                    schema={selectedTool.input_schema}
                    onSubmit={handleRunTool}
                    isLoading={callToolMutation.isPending}
                  />
                ) : (
                  <div className="p-12 text-center text-xs text-[var(--text-muted)] flex flex-col items-center justify-center space-y-2">
                    <Radio className="h-6 w-6 text-white/20 mb-2" />
                    <span>Select a tool from the left panel to configure arguments and execute.</span>
                  </div>
                )}
              </div>

              {/* Result Viewer */}
              {callResult && (
                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border)] pb-2.5">
                    <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                      Execution Result
                    </span>
                    <span
                      className={`text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded-full ${
                        callResult.error || callResult.isError
                          ? "bg-[var(--danger)]/20 text-[var(--danger)]"
                          : "bg-[#26D67C]/20 text-[#26D67C]"
                      }`}
                    >
                      {callResult.error || callResult.isError ? "Error" : "Success"}
                    </span>
                  </div>

                  <pre className="p-4 rounded-xl bg-[#0e0e12] border border-white/5 text-xs font-mono text-[#ECECEF] max-h-72 overflow-y-auto whitespace-pre-wrap select-text">
                    <code>
                      {callResult.content
                        ? JSON.stringify(callResult.content, null, 2)
                        : JSON.stringify(callResult, null, 2)}
                    </code>
                  </pre>
                </div>
              )}
            </div>

            {/* Right Column: Real-Time Protocol Trace (4 cols) */}
            <div className="lg:col-span-4 space-y-4">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                    <Radio className="h-3.5 w-3.5 text-[#26D67C]" />
                    <span>Protocol Trace ({traces.length})</span>
                  </div>
                  {traces.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setTraces([])}
                      className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text)] hover:underline cursor-pointer transition-colors"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="space-y-2.5 max-h-[550px] overflow-y-auto pr-1">
                  {traces.length === 0 ? (
                    <div className="p-12 text-center text-xs text-[var(--text-muted)] flex flex-col items-center justify-center space-y-2">
                      <Terminal className="h-6 w-6 text-white/20 mb-2" />
                      <span>Protocol messages (tools/list, tools/call) will appear here in real time.</span>
                    </div>
                  ) : (
                    traces.map((tr, idx) => {
                      const isOut = tr.direction === "out";

                      return (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-[#0e0e12] border border-white/5 text-xs font-mono space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                isOut
                                  ? "bg-[var(--accent)]/20 text-[var(--accent)]"
                                  : "bg-[#26D67C]/20 text-[#26D67C]"
                              }`}
                            >
                              {tr.direction === "out" ? "Client -> Server" : "Server -> Client"}
                            </span>
                            <span className="text-[10px] text-[var(--text-muted)]">
                              {new Date(tr.timestamp).toLocaleTimeString()}
                            </span>
                          </div>

                          <pre className="text-[11px] text-[#ECECEF] leading-relaxed overflow-x-auto whitespace-pre-wrap select-text max-h-40">
                            <code>{JSON.stringify(tr.payload, null, 2)}</code>
                          </pre>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Navbar>

      {/* Live Mode Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(pendingRunTool)}
        title={`Confirm Live Execution: ${pendingRunTool?.tool.name}`}
        description="You are about to invoke a tool in Live Mode against your remote API. This operation may alter database state or external services."
        confirmButtonText="Execute Live Tool"
        isDestructive={false}
        onConfirm={() => {
          if (pendingRunTool) {
            executeCall(pendingRunTool.tool.name, pendingRunTool.args);
            setPendingRunTool(null);
          }
        }}
        onCancel={() => setPendingRunTool(null)}
      />
    </div>
  );
}

"use client";

import React, { use, useState, useEffect } from "react";
import {
  Play,
  Square,
  Search,
  Radio,
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

  const activeBuild = builds && builds.length > 0 ? builds[0] : null;

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
    if (!activeBuild) return;

    createSessionMutation.mutate(
      {
        build_id: activeBuild.id,
        target: targetMode,
        env_vars: targetMode === "live" ? credentials : {},
      },
      {
        onSuccess: (session) => {
          setSessionId(session.session_id);
          // Memory safety: scrub entered credentials from form memory
          setCredentials({});
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
        <div className="space-y-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)]">Playground</h1>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Test generated MCP tools against an in-process mock server or live API with a real-time protocol trace.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {sessionId ? (
                <button
                  type="button"
                  onClick={handleStopSession}
                  disabled={deleteSessionMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded bg-[var(--danger)]/15 border border-[var(--danger)]/30 text-[var(--danger)] hover:bg-[var(--danger)]/25 transition-all cursor-pointer"
                >
                  <Square className="h-3.5 w-3.5" />
                  <span>Stop Session</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleStartSession}
                  disabled={!activeBuild || createSessionMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
                >
                  <Play className="h-3.5 w-3.5" />
                  <span>
                    {createSessionMutation.isPending ? "Launching..." : "Start Session"}
                  </span>
                </button>
              )}
            </div>
          </div>

          <ProjectStepper projectId={projectId} activeStep="playground" />

          {/* Three-Column Interactive Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Session Controls & Tool List (4 cols) */}
            <div className="lg:col-span-4 space-y-4">
              {/* Session Target Box */}
              <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--text)]">Session Target</span>
                  <span
                    className={`h-2 w-2 rounded-full ${
                      sessionId ? "bg-[#3DD68C] animate-pulse" : "bg-white/20"
                    }`}
                  />
                </div>

                {!sessionId ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 text-xs">
                      <label className="flex items-center gap-1.5 cursor-pointer">
                        <input
                          type="radio"
                          name="target"
                          checked={targetMode === "mock"}
                          onChange={() => setTargetMode("mock")}
                          className="accent-[var(--accent)]"
                        />
                        <span>Mock API (Safe)</span>
                      </label>
                      <label className="flex items-center gap-1.5 cursor-pointer">
                        <input
                          type="radio"
                          name="target"
                          checked={targetMode === "live"}
                          onChange={() => setTargetMode("live")}
                          className="accent-[var(--accent)]"
                        />
                        <span>Live Target API</span>
                      </label>
                    </div>

                    {targetMode === "live" && (
                      <div className="p-2.5 rounded bg-[var(--warning)]/10 border border-[var(--warning)]/30 text-[11px] text-[var(--warning)]">
                        Live mode communicates with real remote endpoints. Non-read-only calls will ask confirmation.
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs font-mono text-[var(--text-muted)] space-y-1">
                    <div>Session ID: {sessionId.slice(0, 16)}...</div>
                    <div className="capitalize">Target: {targetMode} mode</div>
                  </div>
                )}
              </div>

              {/* Tools List */}
              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                    Tools ({tools.length})
                  </span>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    value={toolSearch}
                    onChange={(e) => setToolSearch(e.target.value)}
                    placeholder="Search tools..."
                    className="w-full pl-8 pr-2.5 py-1 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                  />
                  <Search className="absolute left-2.5 top-1.5 h-3.5 w-3.5 text-[var(--text-muted)]" />
                </div>

                <div className="divide-y divide-[var(--border)] max-h-96 overflow-y-auto">
                  {!sessionId ? (
                    <div className="p-4 text-center text-xs text-[var(--text-muted)]">
                      Start session to inspect and test tools.
                    </div>
                  ) : toolsLoading ? (
                    <div className="p-4 text-center text-xs text-[var(--text-muted)]">
                      Listing tools from server...
                    </div>
                  ) : filteredTools.length === 0 ? (
                    <div className="p-4 text-center text-xs text-[var(--text-muted)]">
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
                        className={`w-full py-2.5 px-2 flex flex-col text-left transition-colors cursor-pointer ${
                          selectedTool?.name === t.name
                            ? "bg-white/10 font-medium text-[var(--text)]"
                            : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
                        }`}
                      >
                        <span className="text-xs font-mono font-medium">{t.name}</span>
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
              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 space-y-4 min-h-[300px]">
                <h3 className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider border-b border-[var(--border)] pb-2">
                  Invoke Tool: {selectedTool ? selectedTool.name : "(Select tool)"}
                </h3>

                {selectedTool ? (
                  <SchemaForm
                    schema={selectedTool.input_schema}
                    onSubmit={handleRunTool}
                    isLoading={callToolMutation.isPending}
                  />
                ) : (
                  <div className="p-8 text-center text-xs text-[var(--text-muted)]">
                    Select a tool from the left panel to generate arguments and run.
                  </div>
                )}
              </div>

              {/* Result Viewer */}
              {callResult && (
                <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
                  <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
                    <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                      Execution Result
                    </span>
                    <span
                      className={`text-[11px] font-mono ${
                        callResult.error || callResult.isError
                          ? "text-[var(--danger)]"
                          : "text-[#3DD68C]"
                      }`}
                    >
                      {callResult.error || callResult.isError ? "Error" : "Success"}
                    </span>
                  </div>

                  <pre className="p-3 rounded bg-[#101013] border border-white/5 text-xs font-mono text-[#ECECEF] max-h-60 overflow-y-auto whitespace-pre-wrap select-text">
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
              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
                    <Radio className="h-3.5 w-3.5 text-[var(--accent)]" />
                    <span>Protocol Trace ({traces.length})</span>
                  </div>
                  {traces.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setTraces([])}
                      className="text-[11px] text-[var(--text-muted)] hover:underline cursor-pointer"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="space-y-2 max-h-[550px] overflow-y-auto pr-1">
                  {traces.length === 0 ? (
                    <div className="p-8 text-center text-xs text-[var(--text-muted)]">
                      Protocol messages (tools/list, tools/call) will appear here in real time.
                    </div>
                  ) : (
                    traces.map((tr, idx) => {
                      const isOut = tr.direction === "out";

                      return (
                        <div
                          key={idx}
                          className="p-3 rounded bg-[#101013] border border-white/5 text-xs font-mono space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span
                              className={`px-1.5 py-0.2 rounded text-[10px] font-bold uppercase ${
                                isOut
                                  ? "bg-[var(--accent)]/20 text-[var(--accent)]"
                                  : "bg-[#3DD68C]/20 text-[#3DD68C]"
                              }`}
                            >
                              {tr.direction === "out" ? "Client -> Server" : "Server -> Client"}
                            </span>
                            <span className="text-[10px] text-[var(--text-muted)]">
                              {new Date(tr.timestamp).toLocaleTimeString()}
                            </span>
                          </div>

                          <pre className="text-[11px] text-[#ECECEF] leading-tight overflow-x-auto whitespace-pre-wrap select-text max-h-36">
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

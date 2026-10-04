import React, { useState } from "react";
import { Check, Copy, Terminal, Monitor, Globe } from "lucide-react";
import type { ConnectSnippets } from "@/lib/queries";

interface ConnectPanelProps {
  snippets: ConnectSnippets;
  projectSlug: string;
}

export function ConnectPanel({ snippets, projectSlug }: ConnectPanelProps) {
  const [activeTab, setActiveTab] = useState<"desktop" | "cursor" | "cli" | "http">("desktop");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    } catch {
      // Fallback
    }
  };

  const tabs: { id: "desktop" | "cursor" | "cli" | "http"; label: string; icon: React.ReactNode }[] = [
    { id: "desktop", label: "Claude Desktop", icon: <Monitor className="h-3.5 w-3.5" /> },
    { id: "cursor", label: "Cursor IDE", icon: <Terminal className="h-3.5 w-3.5" /> },
    { id: "cli", label: "CLI (Stdio)", icon: <Terminal className="h-3.5 w-3.5" /> },
    { id: "http", label: "Streamable HTTP", icon: <Globe className="h-3.5 w-3.5" /> },
  ];

  const currentContent =
    activeTab === "desktop"
      ? snippets.claude_desktop
      : activeTab === "cursor"
      ? snippets.cursor
      : activeTab === "cli"
      ? snippets.cli_stdio
      : snippets.cli_http;

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden space-y-4 p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text)]">Connect Your Client</h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Configure {projectSlug} with your preferred desktop or CLI AI client.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1 bg-[var(--surface-raised)] p-1 rounded-md border border-[var(--border)] overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded transition-all cursor-pointer whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-white/10 text-[var(--text)] font-semibold shadow-xs"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Snippet box */}
      <div className="relative rounded-lg border border-[var(--border)] bg-[#101013] p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono text-[var(--text-muted)] uppercase">
            {activeTab === "desktop"
              ? "claude_desktop_config.json"
              : activeTab === "cursor"
              ? ".cursor/mcp.json"
              : "Shell Command"}
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(currentContent, activeTab)}
            className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)] px-2 py-1 rounded hover:bg-white/5 transition-all cursor-pointer"
          >
            {copiedKey === activeTab ? (
              <>
                <Check className="h-3.5 w-3.5 text-[#3DD68C]" />
                <span className="text-[#3DD68C]">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        <pre className="text-xs font-mono text-[#ECECEF] leading-relaxed overflow-x-auto whitespace-pre-wrap select-text">
          <code>{currentContent}</code>
        </pre>
      </div>

      {/* Required Environment Variables */}
      {snippets.required_env_vars && snippets.required_env_vars.length > 0 && (
        <div className="p-3.5 rounded bg-white/[0.02] border border-[var(--border)] space-y-1.5">
          <span className="text-xs font-semibold text-[var(--text)] block">
            Required Environment Variables:
          </span>
          <div className="flex flex-wrap gap-2 pt-1">
            {snippets.required_env_vars.map((v) => (
              <span
                key={v}
                className="font-mono text-xs px-2 py-0.5 rounded bg-white/5 border border-[var(--border)] text-[var(--text)]"
              >
                {v}
              </span>
            ))}
          </div>
          <p className="text-[11px] text-[var(--text-muted)] pt-1">
            Provide these credentials in your local environment or client configuration file.
          </p>
        </div>
      )}
    </div>
  );
}

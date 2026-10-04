import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

interface CodeViewerProps {
  code: string;
  language?: string;
  filename?: string;
  className?: string;
}

export function CodeViewer({
  code,
  language = "python",
  filename,
  className = "",
}: CodeViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div
      className={`rounded-lg border border-[var(--border)] bg-[#101013] overflow-hidden ${className}`}
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border)] bg-[#16161A]/80">
        <div className="flex items-center gap-2">
          {filename && (
            <span className="text-xs font-mono font-medium text-[var(--text)]">
              {filename}
            </span>
          )}
          <span className="text-[10px] font-mono uppercase text-[var(--text-muted)] px-1.5 py-0.5 rounded bg-white/5">
            {language}
          </span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)] px-2 py-1 rounded hover:bg-white/5 transition-all cursor-pointer"
          title="Copy code"
        >
          {copied ? (
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
      <div className="p-4 overflow-x-auto text-xs font-mono leading-relaxed text-[#ECECEF] select-text">
        <pre tabIndex={0}>
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

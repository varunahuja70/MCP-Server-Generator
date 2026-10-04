import React, { useState } from "react";
import { X, Bot } from "lucide-react";

interface DescriptionEditorProps {
  isOpen: boolean;
  toolName: string;
  initialDescription: string;
  onSave: (newDescription: string) => void;
  onClose: () => void;
}

export function DescriptionEditor({
  isOpen,
  toolName,
  initialDescription,
  onSave,
  onClose,
}: DescriptionEditorProps) {
  const [desc, setDesc] = useState(initialDescription);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-xl h-full bg-[var(--surface-raised)] border-l border-[var(--border)] p-6 flex flex-col justify-between shadow-2xl">
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
            <div>
              <h3 className="text-base font-semibold text-[var(--text)]">Edit Description</h3>
              <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                Tool: <span className="text-[var(--accent)]">{toolName}</span>
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-[var(--text-muted)] hover:text-[var(--text)] p-1 rounded hover:bg-white/5 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
              Tool Description
            </label>
            <textarea
              rows={6}
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
            <p className="text-[11px] text-[var(--text-muted)] mt-1">
              Length: {desc.length} characters (max 1,024 recommended).
            </p>
          </div>

          {/* Agent View Preview */}
          <div className="rounded-lg border border-[var(--border)] bg-[#101013] p-4 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
              <Bot className="h-3.5 w-3.5 text-[var(--accent)]" />
              <span>What the Agent Sees</span>
            </div>
            <div className="p-3 rounded bg-[#16161A] border border-white/5 text-xs font-mono text-[#ECECEF] leading-relaxed whitespace-pre-wrap select-text">
              {desc || <span className="text-white/30 italic">No description provided.</span>}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-6 border-t border-[var(--border)]">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 text-xs font-medium rounded text-[var(--text-muted)] hover:text-[var(--text)]"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onSave(desc)}
            className="px-4 py-1.5 text-xs font-medium rounded bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] cursor-pointer"
          >
            Save Description
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmWord?: string;
  confirmButtonText?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmWord,
  confirmButtonText = "Confirm",
  isDestructive = true,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const [typedInput, setTypedInput] = useState("");

  if (!isOpen) return null;

  const isMatches = !confirmWord || typedInput.trim() === confirmWord;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-6 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
              isDestructive ? "bg-[var(--danger)]/15 text-[var(--danger)]" : "bg-[var(--warning)]/15 text-[var(--warning)]"
            }`}
          >
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-[var(--text)]">{title}</h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{description}</p>
          </div>
        </div>

        {confirmWord && (
          <div className="mb-4">
            <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
              Type <span className="font-mono text-[var(--text)] font-bold">{confirmWord}</span> to confirm:
            </label>
            <input
              type="text"
              value={typedInput}
              onChange={(e) => setTypedInput(e.target.value)}
              placeholder={confirmWord}
              className="w-full px-3 py-1.5 text-sm rounded bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onCancel}
            className="px-3.5 py-1.5 text-sm font-medium rounded text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5 transition-all"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!isMatches}
            onClick={() => {
              if (isMatches) {
                onConfirm();
              }
            }}
            className={`px-4 py-1.5 text-sm font-medium rounded transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
              isDestructive
                ? "bg-[var(--danger)] text-white hover:opacity-90"
                : "bg-[var(--accent)] text-white hover:opacity-90"
            }`}
          >
            {confirmButtonText}
          </button>
        </div>
      </div>
    </div>
  );
}

import React from "react";
import { FolderPlus } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  actionText,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface)]">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/5 text-[var(--accent)] mb-4">
        {icon || <FolderPlus className="h-6 w-6" />}
      </div>
      <h3 className="text-base font-semibold text-[var(--text)] mb-1">{title}</h3>
      <p className="text-sm text-[var(--text-muted)] max-w-sm mb-6">{description}</p>
      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md bg-[var(--accent)] text-white hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

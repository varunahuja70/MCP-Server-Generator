import React from "react";
import { Folder, FileText, ChevronRight, ChevronDown } from "lucide-react";
import type { FileTreeItem } from "@/lib/queries";

interface FileTreeProps {
  items: FileTreeItem[];
  selectedPath: string;
  onSelectFile: (path: string) => void;
}

export function FileTree({ items, selectedPath, onSelectFile }: FileTreeProps) {
  const [openDirs, setOpenDirs] = React.useState<Record<string, boolean>>({
    "": true,
  });

  const toggleDir = (dirPath: string) => {
    setOpenDirs((prev) => ({
      ...prev,
      [dirPath]: !prev[dirPath],
    }));
  };

  const renderNodes = (nodes: FileTreeItem[], depth = 0) => {
    return nodes.map((node) => {
      const isDir = node.type === "directory";
      const isSelected = !isDir && node.path === selectedPath;
      const isOpen = openDirs[node.path] ?? true; // default open

      if (isDir) {
        return (
          <div key={node.path} className="select-none">
            <button
              type="button"
              onClick={() => toggleDir(node.path)}
              style={{ paddingLeft: `${depth * 14 + 8}px` }}
              className="w-full flex items-center gap-1.5 py-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5 rounded text-left transition-colors cursor-pointer"
            >
              {isOpen ? (
                <ChevronDown className="h-3.5 w-3.5 shrink-0" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 shrink-0" />
              )}
              <Folder className="h-3.5 w-3.5 shrink-0 text-[var(--accent)]" />
              <span className="font-mono truncate">{node.name}</span>
            </button>
            {isOpen && node.children && (
              <div>{renderNodes(node.children, depth + 1)}</div>
            )}
          </div>
        );
      }

      return (
        <button
          key={node.path}
          type="button"
          onClick={() => onSelectFile(node.path)}
          style={{ paddingLeft: `${depth * 14 + 20}px` }}
          className={`w-full flex items-center gap-2 py-1 text-xs rounded text-left transition-colors cursor-pointer ${
            isSelected
              ? "bg-white/10 text-[var(--text)] font-semibold"
              : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
          }`}
        >
          <FileText className="h-3.5 w-3.5 shrink-0 text-[var(--text-muted)]" />
          <span className="font-mono truncate">{node.name}</span>
          {node.size !== undefined && (
            <span className="ml-auto pr-2 text-[10px] font-mono text-[var(--text-muted)] opacity-60">
              {node.size > 1024 ? `${Math.round(node.size / 1024)}KB` : `${node.size}B`}
            </span>
          )}
        </button>
      );
    });
  };

  return <div className="space-y-0.5">{renderNodes(items)}</div>;
}

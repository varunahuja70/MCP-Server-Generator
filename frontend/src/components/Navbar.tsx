"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Hammer, LogOut } from "lucide-react";
import { useAuthStatus, useLogoutMutation } from "@/lib/queries";
import { ModeBanner } from "@/components/ModeBanner";

interface NavbarProps {
  children: React.ReactNode;
}

export function Navbar({ children }: NavbarProps) {
  const pathname = usePathname();
  const { data: auth } = useAuthStatus();
  const logoutMutation = useLogoutMutation();

  const isExposed = auth?.mode === "exposed";

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)] text-[var(--text)]">
      {auth && <ModeBanner mode={auth.mode} playgroundEnabled={auth.playground_enabled} />}

      <header className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-md">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex h-14 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="flex items-center gap-2.5 font-bold text-sm tracking-tight text-[var(--text)] hover:opacity-90"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--accent)] text-white shadow-sm">
                <Hammer className="h-4 w-4" />
              </div>
              <span>MCP Forge</span>
            </Link>

            <nav className="flex items-center gap-1 sm:gap-2">
              <Link
                href="/"
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  pathname === "/"
                    ? "bg-white/10 text-[var(--text)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
                }`}
              >
                Projects
              </Link>
              <Link
                href="/projects/new"
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  pathname.startsWith("/projects/new")
                    ? "bg-white/10 text-[var(--text)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
                }`}
              >
                New Project
              </Link>
              <Link
                href="/guide"
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  pathname === "/guide"
                    ? "bg-[#26D67C]/15 text-[#26D67C] font-semibold"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5"
                }`}
              >
                Guide (How to Use)
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono border border-[var(--border)] bg-white/5 text-[var(--text-muted)]">
              <span className={`h-1.5 w-1.5 rounded-full ${isExposed ? "bg-[#F5A524]" : "bg-[#3DD68C]"}`} />
              <span>{isExposed ? "Exposed" : "Local"}</span>
            </div>

            {isExposed && auth?.authenticated && (
              <button
                type="button"
                onClick={() => logoutMutation.mutate()}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-white/5 rounded transition-all cursor-pointer"
                title="Log out"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {children}
      </main>
    </div>
  );
}

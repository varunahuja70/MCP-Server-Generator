"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Hammer, Lock, AlertCircle } from "lucide-react";
import { useLoginMutation } from "@/lib/queries";

export default function LoginPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const loginMutation = useLoginMutation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");

    if (!token.trim()) {
      setErrorMsg("Access token is required.");
      return;
    }

    loginMutation.mutate(token.trim(), {
      onSuccess: () => {
        router.push("/");
      },
      onError: (err: Error) => {
        setErrorMsg(err.message || "Invalid access token.");
      },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)] p-4">
      <div className="w-full max-w-sm rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--accent)] text-white mb-3 shadow-sm">
            <Hammer className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--text)]">MCP Forge</h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Access token required in Exposed mode.
          </p>
        </div>

        {errorMsg && (
          <div className="flex items-center gap-2 p-3 mb-4 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-xs text-[var(--danger)]">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="token"
              className="block text-xs font-medium text-[var(--text-muted)] mb-1.5"
            >
              Access Token (<code className="text-[11px]">FORGE_ACCESS_TOKEN</code>)
            </label>
            <div className="relative">
              <input
                id="token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste access token"
                required
                className="w-full pl-9 pr-3 py-2 text-sm rounded-md bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
              />
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-[var(--text-muted)]" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full py-2 px-4 rounded-md bg-[var(--accent)] text-white text-sm font-medium hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
          >
            {loginMutation.isPending ? "Verifying..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

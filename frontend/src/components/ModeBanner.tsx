import React from "react";
import { ShieldAlert } from "lucide-react";

interface ModeBannerProps {
  mode: "local" | "exposed";
  playgroundEnabled?: boolean;
}

export function ModeBanner({ mode, playgroundEnabled }: ModeBannerProps) {
  if (mode === "local") return null;

  return (
    <div className="w-full bg-[#B45309]/15 border-b border-[#B45309]/30 px-4 py-2 text-xs text-[#F5A524] flex items-center justify-between">
      <div className="flex items-center gap-2 max-w-4xl mx-auto w-full">
        <ShieldAlert className="h-4 w-4 shrink-0 text-[#F5A524]" />
        <span>
          <strong className="font-semibold">Exposed Mode:</strong> MCP Forge is bound to a non-loopback network interface. Access token authentication is enforced.
          {!playgroundEnabled && " Live playground is disabled in exposed mode for host defense."}
        </span>
      </div>
    </div>
  );
}

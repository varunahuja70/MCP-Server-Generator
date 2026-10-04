import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { RiskBadge } from "@/components/RiskBadge";
import { MethodPill } from "@/components/MethodPill";
import { ModeBanner } from "@/components/ModeBanner";

describe("Frontend Foundation Shared Components", () => {
  it("renders RiskBadge with explicit text labels", () => {
    const { unmount } = render(<RiskBadge risk="read" />);
    expect(screen.getByText("Read")).toBeDefined();
    unmount();

    const { unmount: u2 } = render(<RiskBadge risk="write" />);
    expect(screen.getByText("Writes")).toBeDefined();
    u2();

    const { unmount: u3 } = render(<RiskBadge risk="destructive" />);
    expect(screen.getByText("Deletes")).toBeDefined();
    u3();
  });

  it("renders MethodPill with uppercase method", () => {
    render(<MethodPill method="get" />);
    expect(screen.getByText("GET")).toBeDefined();
  });

  it("renders ModeBanner only when mode is exposed", () => {
    const { container, rerender } = render(<ModeBanner mode="local" />);
    expect(container.firstChild).toBeNull();

    rerender(<ModeBanner mode="exposed" playgroundEnabled={false} />);
    expect(screen.getByText(/Exposed Mode:/i)).toBeDefined();
    expect(screen.getByText(/Live playground is disabled in exposed mode/i)).toBeDefined();
  });
});

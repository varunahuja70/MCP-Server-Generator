import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SchemaForm } from "@/components/SchemaForm";

describe("SchemaForm component", () => {
  it("renders empty state when tool has no arguments", () => {
    const handleSubmit = vi.fn();
    render(<SchemaForm schema={{ type: "object", properties: {} }} onSubmit={handleSubmit} />);
    expect(screen.getByText(/This tool takes no arguments/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /Run Tool/i })).toBeDefined();
  });

  it("renders primitive inputs according to schema properties", () => {
    const handleSubmit = vi.fn();
    const schema = {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "integer", description: "Max results" },
        active: { type: "boolean" },
      },
      required: ["query"],
    };

    render(<SchemaForm schema={schema} onSubmit={handleSubmit} />);

    expect(screen.getByText("query")).toBeDefined();
    expect(screen.getByText("Search query")).toBeDefined();
    expect(screen.getByText("limit")).toBeDefined();
    expect(screen.getByText("active")).toBeDefined();

    const textInput = screen.getByPlaceholderText("Enter query");
    fireEvent.change(textInput, { target: { value: "hello mcp" } });

    const numberInput = screen.getByRole("spinbutton");
    fireEvent.change(numberInput, { target: { value: "25" } });

    const submitBtn = screen.getByRole("button", { name: /Run Tool/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith({
      query: "hello mcp",
      limit: 25,
    });
  });

  it("supports switching to Raw JSON input and parsing payload", () => {
    const handleSubmit = vi.fn();
    render(<SchemaForm schema={{ type: "object", properties: { city: { type: "string" } } }} onSubmit={handleSubmit} />);

    // Click Raw JSON toggle
    const toggleBtn = screen.getByRole("button", { name: /Raw JSON/i });
    fireEvent.click(toggleBtn);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: '{"city": "San Francisco", "units": "metric"}' } });

    const submitBtn = screen.getByRole("button", { name: /Run Tool/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith({
      city: "San Francisco",
      units: "metric",
    });
  });
});

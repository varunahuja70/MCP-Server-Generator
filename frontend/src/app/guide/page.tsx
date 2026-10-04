"use client";

import React from "react";
import Link from "next/link";
import {
  FileText,
  Hammer,
  Play,
  ShieldCheck,
  Zap,
  ArrowRight,
  CheckCircle2,
  HelpCircle,
  Layers,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";

export default function GuidePage() {
  const steps = [
    {
      step: "01",
      title: "Create or Import Your Project",
      icon: <FileText className="h-5 w-5 text-[#26D67C]" />,
      summary: "Start with an OpenAPI or Swagger specification.",
      details: [
        "Go to 'New Project' from the navigation bar or pick a pre-made sample on the homepage.",
        "Provide your API specification by uploading a file (.json or .yaml), pasting the text, or entering an API URL.",
        "MCP Forge automatically parses all API paths, HTTP methods, and schemas into tool candidates.",
      ],
      quickTip: "Tip: If you don't have an API spec ready, click 'Task Management API' on the homepage to start instantly.",
    },
    {
      step: "02",
      title: "Configure & Curate Tools",
      icon: <Layers className="h-5 w-5 text-[var(--accent)]" />,
      summary: "Choose which API endpoints your AI agent should have access to.",
      details: [
        "By default, all safe read-only operations (GET endpoints) are turned ON.",
        "Write, update, and delete operations are turned OFF by default for security. You can toggle them ON if needed.",
        "Rename tools to clean, human-friendly names (e.g. 'list_tasks', 'create_user') so LLMs understand them easily.",
        "Add clear descriptions explaining what each tool does and what input parameters mean.",
      ],
      quickTip: "Security Rule: Destructive operations always ask for confirmation when running against live servers.",
    },
    {
      step: "03",
      title: "Set Runtime Settings & Review",
      icon: <ShieldCheck className="h-5 w-5 text-[#F5A524]" />,
      summary: "Configure timeouts, base URLs, and run automated security audits.",
      details: [
        "Settings Tab: Set the Base URL of your backend, tool name prefix, request timeouts, and retry policies.",
        "Review Tab: Runs an automatic security and schema audit against the OWASP and MCP standards.",
        "Fix or acknowledge any warnings before proceeding to code generation.",
      ],
      quickTip: "All tokens, passwords, and API keys are read strictly from environment variables, never hardcoded.",
    },
    {
      step: "04",
      title: "Generate Server Code",
      icon: <Hammer className="h-5 w-5 text-[#26D67C]" />,
      summary: "Turn your API spec into a real Python MCP server.",
      details: [
        "Click the green 'Generate Build' button in the Generate tab.",
        "MCP Forge creates a complete project: server runtime, tools.json, Dockerfile, pyproject.toml, and unit tests.",
        "Browse generated code right in the web browser or download the full ZIP archive.",
        "Ready-to-copy connection snippets are available for Claude Desktop, Cursor, and Stdio CLI.",
      ],
      quickTip: "Builds are 100% deterministic: the same input will always produce the exact same server code.",
    },
    {
      step: "05",
      title: "Test in the Interactive Playground",
      icon: <Play className="h-5 w-5 text-[#26D67C]" />,
      summary: "Test tools with zero setup using the built-in Playground.",
      details: [
        "Open the 'Test' (Playground) tab from your project.",
        "Click the vibrant green 'Start Session' button to launch the MCP server in-process.",
        "Choose 'Mock Server' to test safely with simulated data, or 'Live Target API' to make real requests.",
        "Select any tool from the list, fill in the form fields or JSON, and click 'Run Tool'.",
        "Watch the real-time 'Protocol Trace' on the right side to see every JSON-RPC 2.0 message exchanged between client and server.",
      ],
      quickTip: "The Playground runs in an isolated subprocess with strict SSE protocol streaming.",
    },
  ];

  const faqs = [
    {
      q: "What is an MCP server?",
      a: "Model Context Protocol (MCP) allows AI tools (like Claude, Cursor, and custom LLM agents) to securely connect to your backend APIs and execute actions on your behalf.",
    },
    {
      q: "Do I need Python installed to use the Playground?",
      a: "The MCP Forge backend already manages the Python runtime and mock engine for you. Just click 'Start Session' to test your tools immediately.",
    },
    {
      q: "How do I connect the server to Claude Desktop?",
      a: "Go to your project's 'Generate' tab, select a completed build, and look at the 'Connect Client' section. Copy the JSON snippet directly into your claude_desktop_config.json file.",
    },
    {
      q: "Where do my API keys go?",
      a: "Never put secret keys into the OpenAPI file or source code. Copy the `.env.example` file to `.env` in the generated folder and add your API credentials there.",
    },
  ];

  return (
    <Navbar>
      <div className="space-y-12 max-w-[1440px] mx-auto pb-16">
        {/* Hero Header */}
        <div className="relative overflow-hidden rounded-3xl border border-[var(--border)] bg-gradient-to-b from-[var(--surface-raised)] to-[var(--surface)] p-8 sm:p-12 shadow-sm">
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#26D67C]/15 border border-[#26D67C]/30 text-xs font-semibold text-[#26D67C]">
              <Zap className="h-3.5 w-3.5" />
              <span>Step-by-Step User Guide</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--text)]">
              How to Build & Test MCP Servers
            </h1>
            <p className="text-sm sm:text-base text-[var(--text-muted)] leading-relaxed">
              MCP Forge converts your OpenAPI & Swagger descriptions into ready-to-use, secure Model Context Protocol servers for AI agents like Claude Desktop and Cursor. Follow this simple guide to get started in minutes.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <Link
                href="/projects/new"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold rounded-xl bg-[#26D67C] text-black hover:bg-[#20bd6d] active:scale-[0.98] transition-all shadow-md shadow-[#26D67C]/20"
              >
                <span>Create New Project</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href="/"
                className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-xl border border-[var(--border)] bg-white/5 hover:bg-white/10 text-[var(--text)] transition-all"
              >
                <span>View Existing Projects</span>
              </Link>
            </div>
          </div>
        </div>

        {/* 5 Steps Breakdown */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[var(--text)]">5 Easy Steps to Success</h2>
              <p className="text-xs text-[var(--text-muted)] mt-1">From raw API spec to fully tested AI tools.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {steps.map((s) => (
              <div
                key={s.step}
                className="p-6 sm:p-8 rounded-2xl border border-[var(--border)] bg-[var(--surface)] hover:border-white/20 transition-all shadow-sm space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
                  <div className="flex items-center gap-3.5">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--surface-raised)] border border-[var(--border)] shadow-sm">
                      {s.icon}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-white/10 text-[var(--text-muted)] font-bold">
                          Step {s.step}
                        </span>
                        <h3 className="text-base font-semibold text-[var(--text)]">{s.title}</h3>
                      </div>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">{s.summary}</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                      What to do:
                    </h4>
                    <ul className="space-y-2 text-xs text-[var(--text)] leading-relaxed">
                      {s.details.map((d, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="h-4 w-4 text-[#26D67C] shrink-0 mt-0.5" />
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="flex flex-col justify-center p-4 rounded-xl bg-[var(--surface-raised)] border border-[var(--border)] text-xs space-y-2">
                    <span className="font-semibold text-[#26D67C] flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5" /> Pro Tip
                    </span>
                    <p className="text-[var(--text-muted)] leading-relaxed">{s.quickTip}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Frequently Asked Questions */}
        <div className="space-y-6 pt-4">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5 text-[var(--accent)]" />
            <h2 className="text-xl font-bold tracking-tight text-[var(--text)]">Frequently Asked Questions</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {faqs.map((f, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-2 shadow-sm"
              >
                <h3 className="text-sm font-semibold text-[var(--text)]">{f.q}</h3>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">{f.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Reference Summary Card */}
        <div className="p-8 rounded-3xl border border-[#26D67C]/30 bg-gradient-to-r from-[var(--surface)] via-[var(--surface-raised)] to-[var(--surface)] flex flex-col sm:flex-row items-center justify-between gap-6 shadow-md shadow-[#26D67C]/5">
          <div className="space-y-2 text-center sm:text-left">
            <h3 className="text-lg font-bold text-[var(--text)]">Ready to test your first MCP Server?</h3>
            <p className="text-xs text-[var(--text-muted)] max-w-xl">
              Open your project, generate the build files, and click Start Session in the Playground to see your tools live in action.
            </p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 text-xs font-semibold rounded-xl bg-[#26D67C] text-black hover:bg-[#20bd6d] active:scale-[0.98] transition-all shadow-md shadow-[#26D67C]/20 shrink-0"
          >
            <span>Go to My Projects</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </Navbar>
  );
}

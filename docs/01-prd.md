# 01 - Product Requirements (PRD)

Working name: **MCP Forge**
Status: Draft v1
Track: Full (saved projects, a database, a testing UI). No payments, no multi-user accounts.

> Rule for this document: behaviour only. No framework or library names. Standards names (OpenAPI, MCP) are the product's subject and are allowed. The stack is chosen in `02-architecture.md`.

## One-liner

Give MCP Forge an API description (an OpenAPI file or link) and it produces a ready-to-run MCP server for that API, plus a built-in testing screen where you can try every tool before you ship it.

## Problem

Most companies and developers have a working HTTP API. AI agents (Claude and others) can only use it comfortably if it is exposed as an MCP server. Today, making one means:

- reading the MCP documentation and the SDK,
- hand-writing one tool per endpoint,
- guessing how to turn parameters, authentication and errors into something an agent understands,
- finding out only later that the server is unsafe (it exposes delete endpoints), too big (hundreds of tools confuse agents) or badly described (agents call it wrongly).

There is no quick way to preview how an agent will see the API, and no safe way to test the server without wiring it into a real AI app first.

## Target user

**Primary:** A developer or small team that owns or uses an HTTP API with an OpenAPI description and wants AI agents to use it, without learning every detail of MCP.

**Secondary:** Developers who want to study clean generated code; open-source contributors; API providers publishing an MCP server for their customers.

**Not for:** People who need to turn a website into an API (no scraping), or teams that need a hosted multi-tenant platform with accounts and billing.

## Core features (V1)

### 1. Bring an API description in
- Accept an OpenAPI file in JSON or YAML by upload, by pasted text, or by link.
- Supported versions: Swagger 2.0, OpenAPI 3.0, 3.1 and 3.2.
- Show clear, readable errors when the file is invalid, too large, or uses unsupported parts. Never crash on bad input.
- Provide built-in sample APIs so a first-time visitor can try everything without owning a spec.

### 2. Understand the API
- Show a summary: name, version, servers, number of operations, groups (tags), authentication methods found.
- Show every operation with method, path, summary and risk label (read-only, writes data, destructive).

### 3. Decide what the agent can see
- Each operation becomes at most one tool. The user picks which ones are enabled.
- **Safe by default:** read-only operations start enabled; anything that changes or deletes data starts disabled and needs a deliberate switch.
- The user can rename a tool, rewrite its description, and group tools by tag.
- A visible warning appears when too many tools are enabled, because agents work worse with very large tool lists. The tool offers presets (for example "read-only", "by tag").
- Each tool carries honest hints about itself (read-only, destructive, repeat-safe) so agents and apps can decide how careful to be.

### 4. Quality and safety review
- A checklist-style review runs before generation and lists findings with a severity and a suggested fix. It checks for:
  - missing or very short descriptions,
  - name clashes and unclear names,
  - oversized input definitions,
  - unsupported features that will be skipped,
  - **suspicious description text** that tries to instruct an AI agent (hidden characters, "ignore previous instructions" style text), since descriptions go straight into an agent's context,
  - write or delete tools that are enabled.
- Blocking findings must be acknowledged before generation. The user can always see exactly what was changed or removed.

### 5. Connect the API's authentication
- Detect how the API authenticates: API key (header or query), bearer token, basic login, or machine-to-machine token request.
- The generated server reads credentials from its environment at run time. Credentials are never written into generated files.
- The user can set the API base address, request timeout, response size limit and retry behaviour for safe, repeatable requests.

### 6. Generate the server
- Produce a complete, readable, runnable project: the server, the tool definitions, setup instructions, an example environment file, a container file, and tests.
- The server supports running locally as a command for desktop AI apps, and over the network for remote use.
- Every generation is saved as a numbered build with its warnings. Regenerating after a spec change keeps the user's choices (renames, enabled tools) where the operation still exists, and lists what changed.
- Download as one archive, or browse the files in the app.
- Show copy-paste connection snippets for common AI apps and tools.

### 7. Test it before shipping (the Playground)
- Start the generated server inside the app and list its tools exactly as an agent would see them.
- Fill a form built from each tool's input definition, run the tool, and see the result and any error.
- Show the raw protocol messages exchanged for every call, with timings.
- Two targets: a **built-in mock of the API** (no credentials, no risk, answers shaped like the spec says) or the **real API** (credentials typed in for the session only, never saved).
- Clearly warn before any call that changes data on the real API.

### 8. Command-line use
- Everything needed for automation also works without the web screen: check a spec, review it, generate a project, and start the app. This lets teams run generation in their build pipeline.

### 9. Project history
- Saved projects list with spec versions, builds and settings. Delete a project and all its data with one confirmed action.

### 10. Safe by design for self-hosting
- Runs on the user's own machine or server. By default only reachable from that machine. If exposed on a network, it requires an access token.
- No usage tracking or data sent anywhere.

## Non-goals (V1)

- No scraping of human documentation pages. Input is an OpenAPI description.
- No other spec formats yet (Postman collections, GraphQL, gRPC are later).
- No AI-written descriptions in V1 (no calls to model providers). Users edit descriptions by hand.
- Only one output language in V1 (Python). A TypeScript output is a later feature.
- No file upload or multipart request support in generated tools (such operations are listed as skipped).
- No full browser-based login flows (authorization-code style) for the target API.
- No hosted version, no user accounts, no billing.
- No publishing to package registries from inside the app.

## Main user flows

**Quick try (first visit)**
1. Choose a sample API.
2. See its operations and the safe default selection.
3. Press Generate, then open the Playground.
4. Run a tool against the mock API and see the result and protocol trace.

**Real use**
1. Create a project from a file or link.
2. Fix any invalid-spec errors shown.
3. Review operations, enable what the agent should have, rename and re-describe.
4. Set base address and authentication mapping.
5. Read the review findings, resolve or acknowledge them.
6. Generate, test in the Playground against the mock, then against the real API with a read-only call.
7. Download the project or copy the connection snippet.

**API changes**
1. Open the project, upload the new spec version.
2. See added, removed and changed operations. Previous choices carry over.
3. Generate a new build.

## Success criteria

- A first-time user goes from opening the app to a successful mock tool call in under 3 minutes.
- At least five varied real-world OpenAPI files (small, large, Swagger 2.0, 3.0, 3.1) generate without errors, or fail with a clear explanation.
- Every generated project starts, lists its tools, and passes its own tests.
- A deliberately hostile spec (code-like text in names and descriptions, huge nesting, circular references, bad encoding) never causes code execution, a crash, or a hang.
- No credential ever appears in generated files, saved data, logs or the browser's storage.
- Parsing and generating a 5,000-operation spec finishes in a reasonable time on a normal laptop (measured and written down, not guessed).
- A new developer can follow the README and have a working demo in under 10 minutes.

## Open questions

1. Final product name and repository name (working name: MCP Forge, repo `mcp-forge`).
2. Open-source licence: MIT or Apache 2.0.
3. Should the TypeScript output be the first follow-up after V1, or the Postman collection input?
4. Should a later version add optional AI-assisted description rewriting using the user's own key?

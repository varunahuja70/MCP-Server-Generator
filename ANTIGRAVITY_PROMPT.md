# Prompt for Google Antigravity

Paste everything inside the box into Antigravity. Attach either the whole `mcp-forge` folder, or the single file `MCP-Forge-FULL-SPEC.md`.

```
You are the lead engineer building an open-source project called MCP Forge. It goes on my public GitHub as a flagship portfolio project, so quality matters more than speed: clean architecture, readable code, real security, real tests, and a README another developer can follow.

INPUT
I attached the complete spec. It is either the folder `mcp-forge/` (CLAUDE.md, AGENTS.md, docs/01 to 06) or one file, MCP-Forge-FULL-SPEC.md, where each file starts with a marker line like `<!-- FILE: docs/01-prd.md -->`. If it is the single file, first split it into the real files and folders named in the markers. Then create the git repo.

SOURCE OF TRUTH
Read ALL of the spec completely before writing any code. The spec decides the stack, data model, API, folder structure, security rules and build order. If something is unclear, contradictory or impossible, do not guess silently: write the question into `QUESTIONS.md`, choose the safest option that matches the spec, and continue.

WHAT TO DO
Build the whole project by executing tickets T01 to T24 in docs/05-tickets.md, in order, without stopping to ask me between tickets. T25 is a stretch ticket: do it only if everything else is green. For each ticket:
1. Implement it fully (no stubs, no TODO placeholders, no fake data in real code paths).
2. Write the tests the ticket and docs/03-security.md require.
3. Run lint, type checks and tests. Fix every failure.
4. Check the ticket's "done when" condition and prove it (run the command or test).
5. Commit with the message `ticket NN: <title>`.
6. Add one line per ticket to `PROGRESS.md` (ticket, result, anything notable).

HARD RULES
- Versions: never write a dependency version from memory. Install the latest stable release with the package manager, then record the real version in docs/versions.lock.md. Follow the "verified" versus "pin at setup" notes in docs/02-architecture.md. Do not use SQLAlchemy 2.1 beta.
- MCP: the current protocol revision is 2026-07-28 and the official Python SDK is v2 (class `MCPServer`, not `FastMCP`; snake_case fields). Before writing any server or client code, read the SDK documentation and the spec pages linked in docs/02-architecture.md section 11, and write the facts you rely on into docs/sdk-notes.md. If something in the spec docs contradicts the SDK docs, follow the SDK docs and note it.
- Security: the central rule is that text from the uploaded API description NEVER goes into generated source code. It lives in tools.json only. Every rule and all 12 required tests in docs/03-security.md are mandatory. No secret may ever appear in logs, errors, API responses, traces, generated files or git.
- Safe defaults: only read-only tools enabled by default, private network targets blocked, credentials only from environment variables.
- Client configs: before writing the connection snippets for desktop AI apps and command-line clients, check each one's current official documentation for the exact config format.
- Numbers: benchmarks, compatibility results and README claims must come from real runs you do. Never invent numbers, results or screenshots. Test with real public OpenAPI files as described in T23.
- Design: the dashboard must follow docs/04-frontend.md (premium, minimal, Linear/Vercel quality, dark first, all four states on every screen, accessible).
- Do not add features, services or dependencies that are not in the spec.
- Everything must run with `docker compose up`, and the sample-based demo (generate, mock Playground, trace) must work with no API keys and no internet beyond installing dependencies.

IF YOU GET STUCK
If a ticket still fails after 3 serious attempts, write the details in `BLOCKERS.md` (what failed, what you tried, the error) and move on to tickets that do not depend on it. Return to blocked tickets at the end.

FINISH
After T24 (and T25 if done), do a final verification pass and write `FINAL_REPORT.md` containing:
1. A checklist of every PRD feature with pass or fail and the evidence (test name or command).
2. A checklist of the 12 security tests with pass or fail.
3. The compatibility results and real benchmark numbers.
4. The result of: fresh clone, follow README only, reach a working mock tool call with a visible trace.
5. Open questions, blockers and known limitations, stated honestly.
Do not claim anything works unless you ran it.
```

## Notes for Varun
- Ek hi baar mein 100% perfect nahi aayega. 24 tickets hain, isliye Antigravity beech mein ruk sakta hai ya kuch fail ho sakta hai. `BLOCKERS.md` aur `FINAL_REPORT.md` isi liye hain: aakhir mein dekho kya pass hua aur kya fail.
- Agar beech mein ruk jaye ya context bhar jaye, nayi chat mein bolo: "Read CLAUDE.md, PROGRESS.md and BLOCKERS.md, then continue from the next unfinished ticket with the same rules."
- Is project ko chalane ke liye koi paid API key nahi chahiye. Mock API se poora demo chalta hai. Real API se test karna ho toh us API ki apni key chahiye.
- MCP ka naya version (2026-07-28) aur Python SDK v2 abhi naye hain. Agar Antigravity SDK ke kisi function par atke, toh woh `docs/sdk-notes.md` mein likhega. Wahan dekh lena.
- T25 (TypeScript output) optional hai. Pehle V1 poora pakka karna zyada zaroori hai.

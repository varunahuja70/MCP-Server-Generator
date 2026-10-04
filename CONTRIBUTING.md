# Contributing to MCP Forge

Thank you for your interest in contributing to MCP Forge! We welcome bug reports, improvements to OpenAPI standard coverage, security audits, and pull requests.

## Development Setup

### Prerequisites
- Python 3.13 or 3.14 with [`uv`](https://github.com/astral-sh/uv)
- Node.js 22+ with `pnpm`
- Git

### Initializing the Workspace
```bash
# Clone the repository
git clone https://github.com/your-org/mcp-forge.git
cd mcp-forge

# Install backend dependencies
cd backend
uv sync

# Install frontend dependencies
cd ../frontend
pnpm install
```

### Running Local Development Servers
```bash
# In the root repository directory
make dev
```
This runs the FastAPI backend on `http://127.0.0.1:8000` and the Next.js frontend on `http://127.0.0.1:3000` with hot reloading.

---

## Code Quality Standards

MCP Forge maintains strict code hygiene and security guarantees:

1. **Backend Testing & Types:**
   - Run tests: `uv run pytest` (all tests must pass with zero failures).
   - Format and lint: `uv run ruff check .` and `uv run ruff format .`
   - Static type checking: `uv run mypy src/ tests/` (must pass in strict mode).

2. **Frontend Testing & Types:**
   - Run tests: `pnpm test`
   - Run linter: `pnpm lint`
   - Production build: `pnpm build` (TypeScript check must pass).

3. **Core Architectural Invariants:**
   - **Never place user-derived or specification-derived text into Python code templates.** Spec metadata belongs exclusively in `tools.json`.
   - Tool identifiers must strictly match `^[a-z][a-z0-9_]{0,63}$`.
   - Always run the SSRF validator on any outbound network connection or redirect.
   - Do not add external analytics, third-party fonts, or tracking scripts to the frontend.

---

## Commit Guidelines

When committing changes, please follow the ticket or descriptive convention:
- `ticket NN: <short summary>`
- `fix: <description of fix>`
- `feat: <description of feature>`

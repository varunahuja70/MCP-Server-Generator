# 04 - Frontend

Reads: `01-prd.md`, `02-architecture.md`. A Next.js dashboard that talks to the Forge API on the same origin.

## 1. Design direction
Premium, minimal, calm, developer-grade. Quality bar: Linear and Vercel. Dark first, light supported. Thin borders, generous whitespace, one accent colour, restrained motion. Code and JSON are first-class: monospace blocks are clean, copyable and readable. No decorative gradients, no emoji icons, no stock art.

## 2. Design tokens (`src/styles/tokens.css`, exposed through Tailwind v4 theme variables)
| Token | Dark | Light |
|---|---|---|
| background | `#09090B` | `#FFFFFF` |
| surface | `#101013` | `#FAFAFA` |
| surface-raised | `#16161A` | `#FFFFFF` |
| border | `#25252B` | `#E6E6EA` |
| text | `#ECECEF` | `#0B0B0C` |
| text-muted | `#8A8A93` | `#6A6A72` |
| accent | `#7C5CFF` | `#5B3FE0` |
| success | `#3DD68C` | `#15803D` |
| warning | `#F5A524` | `#B45309` |
| danger | `#F5555D` | `#DC2626` |
| risk-read | `#3DD68C` | `#15803D` |
| risk-write | `#F5A524` | `#B45309` |
| risk-destructive | `#F5555D` | `#DC2626` |

Fonts: Inter (UI) and JetBrains Mono (code), loaded through `next/font` (self-hosted, no external requests). Numbers use tabular figures. Type scale 12/13/14/16/20/28/36. Radius 8 cards, 6 inputs. 4 px spacing grid. Motion 150-200 ms ease-out, always respecting reduced-motion. Risk is never shown by colour alone: each badge also has a text label ("Read", "Writes", "Deletes").

## 3. Screens
1. **Home** (`/`): recent projects, "New project" button, and a "Try a sample API" strip with the bundled samples. Empty state teaches the three-step flow.
2. **New project** (`/projects/new`): three tabs - Upload, Paste, Link - plus samples. After submit: live validation result (version detected, operations count, errors with line/path). Errors are readable and point to the exact location.
3. **Project overview** (`/projects/[id]`): spec summary (name, version, servers, auth methods, tag list), operation counts by risk, latest build status, spec version history, and a stepper showing progress: Import, Tools, Settings, Review, Generate, Test.
4. **Tools** (`/projects/[id]/tools`): the central screen. Table of operations: enabled switch, method pill, path, tool name (inline editable), risk badge, group (tag), description (opens editor drawer with a live "what the agent sees" preview). Filters by tag, method, risk, text. Bulk actions and presets (Read-only, By tag). A running count of enabled tools with a warning bar over the recommended limit. Skipped operations appear greyed with the reason.
5. **Settings** (`/projects/[id]/settings`): base address, timeout, response size limit, retries, naming style, prefix, auth mapping (scheme to environment variable names), transports.
6. **Review** (`/projects/[id]/review`): findings grouped by severity with code, message, location, suggestion, and an "Acknowledge" action for blocking ones. A diff-style view shows the original vs. cleaned text when characters were stripped.
7. **Generate / Builds** (`/projects/[id]/builds`): build button, build list with status and warnings, and for each build a file browser (tree + syntax-highlighted viewer, copy button), Download archive, and a **Connect** panel with ready snippets (desktop app config, command-line client command, remote URL form) and the environment variable list. Spec change diff (added/removed/changed operations) shown when a new spec version exists.
8. **Playground** (`/projects/[id]/playground`): left - session controls (target: Mock or Live, credentials fields for live shown only for Live, Start/Stop); middle - tool list with search, and for the selected tool a generated form, Run button, result viewer (formatted text/JSON, error state); right - protocol trace (list of messages with direction, method, timing; expandable JSON; filter; copy). Live mode shows a warning banner and asks confirmation before non-read-only tools.
9. **Settings (app)** (`/settings`): version, mode (local/exposed), data location, retention, access token status, theme.
10. **Login** (`/login`): only in exposed mode.

## 4. Component inventory
shadcn/ui primitives: Button, Input, Textarea, Select, Switch, Checkbox, Dialog, Sheet, Tabs, Table, Badge, Tooltip, Toast, Skeleton, DropdownMenu, Command, Progress.
Custom: `Stepper`, `SpecDropzone`, `ValidationReport`, `OperationTable`, `RiskBadge`, `MethodPill`, `ToolNameInput`, `DescriptionEditor` (with agent-view preview), `ToolBudgetBar`, `FindingList`, `TextDiff`, `FileTree`, `CodeViewer` (Shiki, plain-text safe), `ConnectPanel`, `SchemaForm`, `ResultViewer`, `TraceList`, `TraceMessage`, `CredentialFields` (password inputs, memory-only), `ConfirmDialog` (type the project name for destructive actions), `EmptyState`, `ErrorState`, `ModeBanner`.

## 5. States (every screen defines all four)
| State | Behaviour |
|---|---|
| Loading | Skeletons matching the layout; no page-level spinners. Long operations (generate, start session) show progress text and are cancellable. |
| Empty | One sentence and the single next action (for example "Import an API description"). |
| Error | Plain language, error code in muted text, a retry button. Validation errors list location and fix hint. |
| Success | Quiet toast; the changed thing updates in place. |

Big lists (operations up to 20,000) use virtualized rows and server-side filtering. Long traces are virtualized and capped with a "load older" control.

## 6. Responsive behaviour
Desktop first, usable down to 360 px. Three-column Playground collapses into tabs (Tools / Run / Trace) below 1024 px. Sidebar collapses to a top bar with a sheet menu below 768 px. Tables scroll inside their container; the page never scrolls sideways. Touch targets 44 px minimum.

## 7. Accessibility floor
- WCAG 2.2 AA contrast in both themes.
- Full keyboard use with a visible 2 px focus ring; logical tab order; dialogs trap and restore focus; Escape closes sheets and dialogs; table rows operable by keyboard.
- Icons that carry meaning have text or `aria-label`. Risk and severity are conveyed with text, not only colour.
- Forms: labels tied to inputs, errors linked by `aria-describedby`, errors announced politely. The generated tool form follows the same rules.
- Trace and results regions are labelled; live updates use polite announcements and can be paused.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`, with a manual theme switch.

## 8. Frontend rules
- TypeScript strict, no `any`. API types generated from the backend OpenAPI schema so client and server cannot drift.
- All server data via TanStack Query hooks in `src/lib/queries`; no fetch calls in components. Every state-changing call sends the `X-Forge-Request: 1` header.
- Spec text, descriptions, results and traces are rendered as escaped text only. Never `dangerouslySetInnerHTML` for any of them.
- Live credentials live only in component state while the Playground session is being created. Never in URLs, local/session storage or the query cache; fields are cleared after the request is sent.
- The schema form supports string (formats: date, date-time, email, uri), number, integer, boolean, enum, array, object, oneOf/anyOf (pick a branch), with a raw JSON fallback editor for anything unsupported. It validates before sending and shows server validation errors per field.
- No third-party scripts, analytics or external fonts. The strict CSP depends on this.
- Tests: Vitest for formatters, the schema form, risk badge logic; Playwright smoke flow (sample project, generate, mock call, see trace).

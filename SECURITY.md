# Security Policy

MCP Forge is a security-focused tool designed to safely generate Model Context Protocol servers from potentially untrusted or malicious OpenAPI/Swagger descriptions. We take security vulnerabilities seriously.

## Supported Versions

| Version | Supported |
|---|---|
| `0.1.x` | ✅ Yes |
| `< 0.1.0` | ❌ No |

---

## Reporting a Vulnerability

Please **DO NOT** report security vulnerabilities through public GitHub issues or discussions.

Instead, please report security vulnerabilities privately via GitHub Security Advisories at:
https://github.com/varunahuja70/MCP-Server-Generator/security/advisories/new

### What to Include in Your Report
To help us investigate and patch the issue quickly, please provide:
1. A clear description of the vulnerability (e.g., SSRF bypass, code injection, token leakage, path traversal).
2. A minimal reproducible example, such as a proof-of-concept OpenAPI specification file or HTTP request sequence.
3. The affected component (`backend/core`, `cli`, `playground`, `frontend`).
4. Any potential remediation or patch suggestions.

### Response Timeline
- **Initial acknowledgement:** Within 48 hours.
- **Vulnerability assessment and fix target:** Within 7 business days.
- **Coordinated disclosure:** We will coordinate the release of a security advisory and patch with the reporter.

---

## Core Security Invariants
When auditing or contributing to MCP Forge, keep these non-negotiable boundaries in mind:
- User-supplied strings must never be evaluated, executed, or interpolated into Python source code.
- Remote network requests must be validated against loopback, private RFC1918, carrier-grade NAT, and cloud metadata targets before connection, and at every redirect step.
- Secrets and tokens must never be written to stdout in stdio mode or stored in traces/database rows.

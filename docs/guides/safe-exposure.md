# Safely Exposing MCP Forge and Generated Servers

By default, MCP Forge runs in `local` mode bound to loopback (`127.0.0.1`), requiring zero authentication. When deploying Forge or generated MCP servers to a remote server, container cluster, or internal VPC, follow these security practices.

---

## 1. Exposing the MCP Forge Web UI / API

To run MCP Forge on a network interface other than loopback:

1. **Set `FORGE_MODE=exposed`:**
   Forge will strictly refuse to start if `FORGE_MODE=exposed` and `FORGE_ACCESS_TOKEN` is unset or blank.
2. **Configure a Strong Access Token:**
   Generate a cryptographically secure random token (e.g. `openssl rand -hex 32`):
   ```bash
   export FORGE_MODE=exposed
   export FORGE_ACCESS_TOKEN=9f8e7d6c5b4a3210fedcba9876543210
   ```
3. **Use HTTPS via Reverse Proxy:**
   Place Forge behind an SSL/TLS terminating reverse proxy (Caddy, NGINX, Cloudflare Tunnel, or AWS ALB). Do not expose raw HTTP over public networks.
4. **Playground Protection:**
   In exposed mode, live target playground invocation is disabled by default to prevent users from abusing the server as an open HTTP proxy.

---

## 2. Exposing Generated MCP Servers via Streamable HTTP

Generated servers support Streamable HTTP transport:
```bash
python server.py --http --host 0.0.0.0 --port 8080
```

### Mandatory Non-Loopback Security Requirements:
- **`MCP_AUTH_TOKEN`:** If the server detects binding to any host other than loopback (`127.0.0.1`, `localhost`), it **refuses to start** unless `MCP_AUTH_TOKEN` is provided in the environment.
- **Header Protection:** Incoming HTTP requests must supply `Authorization: Bearer <MCP_AUTH_TOKEN>`.
- **Host & Origin Validation:** The server strictly checks `Host` and `Origin` headers against allowed domains to mitigate DNS rebinding and cross-site hijacking attacks.
- **Private Target Isolation:** If `ALLOW_PRIVATE_TARGETS=false` (default), the server's runtime SSRF guard rejects any upstream requests directed toward RFC1918 subnets or cloud instance metadata endpoints.

# Connecting Generated Servers to Desktop AI Apps

MCP Forge generates production-ready MCP servers that integrate directly with Model Context Protocol client applications such as **Claude Desktop** and **Cursor**.

---

## 1. Connecting to Claude Desktop

Claude Desktop connects to MCP servers over standard input/output (`stdio`).

### Step 1: Locate Claude Desktop Configuration
Depending on your platform, open `claude_desktop_config.json`:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### Step 2: Add Your Server Configuration
Add an entry under the `mcpServers` object pointing to your generated server:

```json
{
  "mcpServers": {
    "my-api-server": {
      "command": "python",
      "args": [
        "/path/to/my-api-server/server.py"
      ],
      "env": {
        "API_BASE_URL": "https://api.example.com",
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

> **Note on Virtual Environments:** If your generated server uses dependencies in a virtual environment, use the python interpreter inside that environment (e.g. `/path/to/my-api-server/.venv/bin/python` or `.venv/Scripts/python.exe`).

### Step 3: Restart Claude Desktop
Completely quit and restart Claude Desktop. The hammer/tools icon in Claude will indicate that your new tools are active and ready for queries.

---

## 2. Connecting to Cursor

Cursor supports Model Context Protocol servers in both stdio and Streamable HTTP modes.

1. Open **Cursor Settings** > **Features** > **MCP Servers**.
2. Click **Add New MCP Server**.
3. Fill in:
   - **Name:** `my-api-server`
   - **Type:** `stdio` (or `http` if running with `--http`)
   - **Command:** `python /path/to/my-api-server/server.py`
4. Save and verify the status indicator turns green.

# 🚀 Amazing MCP Tools

> **Give your AI agent superpowers — one MCP tool at a time.**

A growing collection of production-ready [MCP (Model Context Protocol)](https://modelcontextprotocol.io) servers that supercharge Claude, Gemini, OpenAI Agents, and any MCP-compatible AI with real-world capabilities.

No API keys. No bloat. Just tools that work.

---

## 🧰 Tools

| Tool | What It Does | Status |
|------|-------------|--------|
| [🎬 video_understanding](./tools/video_understanding/) | Transcripts, metadata & chapters from any YouTube URL | ✅ Live |
| More coming soon... | | 🔜 |

---

## 🎬 Tool #1 — Video Understanding

> **The missing tool for AI agents to understand video content.**

When your AI agent encounters a YouTube URL, it currently gets *nothing* useful back. This MCP server fixes that — returning structured, chaptered transcripts with full metadata, everything an LLM needs to deeply understand and discuss any video.

### What it can do

| Function | Description |
|----------|-------------|
| `video_understand` | **Full analysis** — metadata + chaptered transcript + stats. Use this by default. |
| `video_get_transcript` | Raw timestamped transcript with optional translation |
| `video_get_metadata` | Fast title / author / thumbnail lookup (no transcript fetch) |
| `video_search_transcript` | Find exactly where a topic is discussed, with timestamps |

### Example output

```
video_understand("https://youtube.com/watch?v=O-0poNv2jD4")

→ Title:    The $285B Sell-Off Was Just the Beginning
→ Author:   AI News & Strategy Daily
→ Duration: 29:16  |  Words: 4,774  |  Chapters: 6

Chapter 1 [0:00–5:00]
"The web is forking in the age of agents. Coinbase launched
Agentic Wallets. Cloudflare shipped Markdown for agents..."

Chapter 2 [5:00–10:00] ...
```

---

## ⚡ Quickstart

### 1. Install dependencies

```bash
git clone https://github.com/wjlgatech/amazing_mcp
cd amazing_mcp/tools/video_understanding
pip install -r requirements.txt
```

---

## 🔌 Connect Your AI

### Claude Desktop (GUI)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "video-understanding": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/video_understanding/server.py"]
    }
  }
}
```

Restart Claude Desktop. The tools appear automatically — no manual server start needed.

---

### Claude Code (CLI)

Add the server to your Claude Code MCP config:

```bash
claude mcp add video-understanding python3 /path/to/amazing_mcp/tools/video_understanding/server.py
```

Or manually edit `~/.claude/mcp_servers.json`:

```json
{
  "video-understanding": {
    "command": "python3",
    "args": ["/path/to/amazing_mcp/tools/video_understanding/server.py"]
  }
}
```

Then in any Claude Code session just ask:
> *"Summarize this video: https://youtube.com/watch?v=..."*

---

### Gemini CLI

Install the [Gemini CLI](https://github.com/google-gemini/gemini-cli) then register the MCP server:

```bash
# In your Gemini CLI settings file (~/.gemini/settings.json)
{
  "mcpServers": {
    "video-understanding": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/video_understanding/server.py"]
    }
  }
}
```

Then:
```
gemini> What does this video say about AI agents? https://youtube.com/watch?v=...
```

---

### OpenAI Agents SDK

```python
from agents import Agent, MCPServerStdio

async def main():
    server = MCPServerStdio(
        params={
            "command": "python3",
            "args": ["/path/to/amazing_mcp/tools/video_understanding/server.py"],
        }
    )
    async with server:
        agent = Agent(
            name="Video Analyst",
            instructions="You are an expert at analyzing video content.",
            mcp_servers=[server],
        )
        result = await agent.run(
            "Summarize this video: https://www.youtube.com/watch?v=O-0poNv2jD4"
        )
        print(result.final_output)
```

---

### Any MCP Client (Generic)

The server speaks standard **MCP over stdio**. If your client supports MCP, connect it with:

```
command: python3
args:    ["/path/to/amazing_mcp/tools/video_understanding/server.py"]
```

---

## 🗺️ Roadmap

Tools being built next:

- 🌐 **web_scraper** — Extract clean content from any URL for AI consumption
- 🐦 **twitter_thread** — Unroll and summarize Twitter/X threads
- 📄 **pdf_reader** — Parse and chunk PDFs with page-level citations
- 🔎 **web_search** — Live search results without an API key
- 📊 **csv_analyst** — Query and visualize CSVs in natural language

**Want a tool built?** [Open an issue](https://github.com/wjlgatech/amazing_mcp/issues) →

---

## 🤝 Contributing

1. Fork the repo
2. Create your tool under `tools/your_tool_name/`
3. Include `server.py` + `requirements.txt`
4. Open a PR — if it's useful, it ships

---

## 📄 License

MIT — use freely, attribution appreciated.

---

<p align="center">
  Built by <a href="https://huggingface.co/wjlgatech">@wjlgatech</a> · Star ⭐ if this saves you time
</p>

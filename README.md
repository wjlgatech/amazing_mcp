# 🚀 Amazing MCP Tools

> **Give your AI agent superpowers — one MCP tool at a time.**

A growing collection of production-ready [MCP (Model Context Protocol)](https://modelcontextprotocol.io) servers that supercharge Claude, Gemini, OpenAI Agents, and any MCP-compatible AI with real-world capabilities.

No bloat. No cloud lock-in. Tools that actually work.

---

## 🧰 Tools

| # | Tool | What It Does | Auth needed |
|---|------|-------------|-------------|
| 1 | [🎬 video_understanding](./tools/video_understanding/) | Transcripts, chapters & metadata from any YouTube URL | None |
| 2 | [🐦 twitter_thread](./tools/twitter_thread/) | Unroll, read & search Twitter/X threads | X account (free) |
| 3 | [💼 linkedin](./tools/linkedin/) | Post, read profiles & feed on LinkedIn | LinkedIn account |
| — | More coming... | web scraper · PDF reader · web search | |

---

## 🎬 Tool #1 — Video Understanding

> The missing tool for AI agents to understand video content.

When your AI encounters a YouTube URL, it gets nothing useful back. This fixes that.

### Tools
| Function | Description |
|----------|-------------|
| `video_understand` | **Full analysis** — metadata + chaptered transcript + stats |
| `video_get_transcript` | Raw timestamped transcript, with optional translation |
| `video_get_metadata` | Fast title / author / thumbnail (no transcript fetch) |
| `video_search_transcript` | Find exactly where a topic is discussed |

### Quickstart
```bash
pip install mcp youtube-transcript-api httpx
```
No API key needed. Works immediately.

---

## 🐦 Tool #2 — Twitter/X Thread Unroller

> Unroll full threads, search tweets, read your timeline — no $200/month API.

Twitter's official API now costs **$200/month minimum** just to read tweets.
This MCP server uses Twitter's internal GraphQL API (same as the browser) via
[twikit](https://github.com/d60/twikit) — free, no API key, just a real account.

### Tools
| Function | Description |
|----------|-------------|
| `thread_unroll` | **Unroll a full thread** from any tweet URL — ordered, full text, stats |
| `tweet_get` | Get a single tweet's full details |
| `twitter_search` | Search tweets with full operator support (`from:`, `since:`, etc.) |
| `twitter_get_timeline` | Read your home timeline |

### Quickstart
```bash
pip install mcp twikit
```

```bash
# Set in your MCP config or .env:
TWITTER_USERNAME=your_username
TWITTER_EMAIL=your@email.com
TWITTER_PASSWORD=your_password
```

Cookies are saved after first login — no repeated logins needed.

### Example
```
thread_unroll("https://x.com/sama/status/1234567890")

→ Author: sama (Sam Altman)
→ Tweets: 12  |  Total likes: 48,200
→ [1/12] We're releasing...
→ [2/12] The key insight is...
→ ...
→ full_text: complete thread as one block, ready for LLM analysis
```

---

## 💼 Tool #3 — LinkedIn

> Post to LinkedIn + read profiles & feed — official API for writing, Voyager for reading.

**The state of LinkedIn APIs in 2026:**
LinkedIn's official read scope (`r_member_social`) is **closed to new developers**.
So we combine two approaches: the official API for safe posting, and the
unofficial [linkedin-api](https://pypi.org/project/linkedin-api/) Voyager library for reading.

### Tools
| Function | Auth | ToS | Description |
|----------|------|-----|-------------|
| `linkedin_post` | Official API | ✅ Safe | Post text or link to your profile |
| `linkedin_get_my_urn` | Official API | ✅ Safe | Get your Person URN (one-time setup) |
| `linkedin_get_profile` | Unofficial | ⚠️ ToS risk | Read any profile by username |
| `linkedin_get_profile_posts` | Unofficial | ⚠️ ToS risk | Get recent posts from any profile |
| `linkedin_get_feed` | Unofficial | ⚠️ ToS risk | Read your home feed |
| `linkedin_search_people` | Unofficial | ⚠️ ToS risk | Search people by name/title/company |

### Quickstart
```bash
pip install mcp linkedin-api httpx
```

**For posting (one-time setup):**
1. Create a LinkedIn app at [developer.linkedin.com](https://developer.linkedin.com)
2. Add the **"Share on LinkedIn"** product (self-service, approved in minutes)
3. Complete the OAuth flow to get your access token (scope: `w_member_social openid profile email`)
4. Run `linkedin_get_my_urn()` to get your Person URN
5. Set both as env vars

```bash
LINKEDIN_ACCESS_TOKEN=your_oauth_token
LINKEDIN_PERSON_URN=urn:li:person:XXXXXXX

# For reading (unofficial):
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password
```

**Example — post to LinkedIn:**
```
linkedin_post(
  text="Just shipped a new MCP server for LinkedIn! 🚀\n\nNow Claude can post,
        read profiles, and browse your feed directly.",
  url="https://github.com/wjlgatech/amazing_mcp",
  url_title="Amazing MCP Tools"
)
→ { "success": true, "post_id": "urn:li:share:..." }
```

**Example — research a person:**
```
linkedin_get_profile("satya-nadella")
→ Name, headline, experience at Microsoft, education, 20 top skills
```

---

## 🔌 Connect Your AI

### Claude Desktop
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "video-understanding": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/video_understanding/server.py"]
    },
    "twitter-thread": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/twitter_thread/server.py"],
      "env": {
        "TWITTER_USERNAME": "your_username",
        "TWITTER_EMAIL": "your@email.com",
        "TWITTER_PASSWORD": "your_password"
      }
    },
    "linkedin": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/linkedin/server.py"],
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "your_token",
        "LINKEDIN_PERSON_URN": "urn:li:person:XXXXX",
        "LINKEDIN_EMAIL": "your@email.com",
        "LINKEDIN_PASSWORD": "your_password"
      }
    }
  }
}
```

Restart Claude Desktop. Tools appear automatically — no manual server management.

---

### Claude Code (CLI)
```bash
claude mcp add video-understanding python3 /path/to/amazing_mcp/tools/video_understanding/server.py

claude mcp add twitter-thread \
  -e TWITTER_USERNAME=your_username \
  -e TWITTER_EMAIL=your@email.com \
  -e TWITTER_PASSWORD=your_password \
  -- python3 /path/to/amazing_mcp/tools/twitter_thread/server.py

claude mcp add linkedin \
  -e LINKEDIN_ACCESS_TOKEN=your_token \
  -e LINKEDIN_PERSON_URN=urn:li:person:XXXXX \
  -e LINKEDIN_EMAIL=your@email.com \
  -e LINKEDIN_PASSWORD=your_password \
  -- python3 /path/to/amazing_mcp/tools/linkedin/server.py
```

---

### Gemini CLI
Edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "video-understanding": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/video_understanding/server.py"]
    },
    "twitter-thread": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/twitter_thread/server.py"],
      "env": {
        "TWITTER_USERNAME": "your_username",
        "TWITTER_EMAIL": "your@email.com",
        "TWITTER_PASSWORD": "your_password"
      }
    },
    "linkedin": {
      "command": "python3",
      "args": ["/path/to/amazing_mcp/tools/linkedin/server.py"],
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "your_token",
        "LINKEDIN_PERSON_URN": "urn:li:person:XXXXX",
        "LINKEDIN_EMAIL": "your@email.com",
        "LINKEDIN_PASSWORD": "your_password"
      }
    }
  }
}
```

---

### OpenAI Agents SDK

```python
from agents import Agent, MCPServerStdio

async def main():
    twitter = MCPServerStdio(params={
        "command": "python3",
        "args": ["/path/to/amazing_mcp/tools/twitter_thread/server.py"],
        "env": {
            "TWITTER_USERNAME": "your_username",
            "TWITTER_EMAIL": "your@email.com",
            "TWITTER_PASSWORD": "your_password",
        },
    })
    linkedin = MCPServerStdio(params={
        "command": "python3",
        "args": ["/path/to/amazing_mcp/tools/linkedin/server.py"],
        "env": {
            "LINKEDIN_ACCESS_TOKEN": "your_token",
            "LINKEDIN_PERSON_URN": "urn:li:person:XXXXX",
        },
    })
    async with twitter, linkedin:
        agent = Agent(
            name="Social Media Analyst",
            instructions="You analyze social media content and can post to LinkedIn.",
            mcp_servers=[twitter, linkedin],
        )
        result = await agent.run(
            "Unroll this thread and write a LinkedIn post summarizing the key insights: "
            "https://x.com/sama/status/1234567890"
        )
        print(result.final_output)
```

---

## 🗺️ Roadmap

| Tool | Description | Status |
|------|-------------|--------|
| 🌐 web_scraper | Extract clean content from any URL | 🔜 Next |
| 📄 pdf_reader | Parse PDFs with page-level citations | 🔜 |
| 🔎 web_search | Live search results, no API key | 🔜 |
| 📊 csv_analyst | Query and visualize CSVs in natural language | 🔜 |
| 📧 gmail | Read, draft, and send emails | 🔜 |

**Want a specific tool?** [Open an issue](https://github.com/wjlgatech/amazing_mcp/issues) →

---

## 🤝 Contributing

1. Fork the repo
2. Create your tool under `tools/your_tool_name/`
3. Include `server.py` + `requirements.txt`
4. One server per tool, MCP stdio transport, FastMCP pattern
5. Open a PR

---

## ⚠️ Disclaimer

Some tools use unofficial APIs that may violate the ToS of the respective platforms.
Use them responsibly, with your own accounts, at reasonable request rates.
The authors are not responsible for account bans or other consequences.

---

## 📄 License

MIT — use freely, attribution appreciated.

---

<p align="center">
  Built by <a href="https://huggingface.co/wjlgatech">@wjlgatech</a> · Star ⭐ if this saves you time
</p>

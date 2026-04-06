# LICTER MCP Server — Brand Intelligence for LLMs

Connect Claude Desktop, ChatGPT, or Cursor directly to LICTER's real-time brand monitoring data.

## Quick Start

```bash
pip install fastmcp
python licter-mcp/server.py
```

## Claude Desktop Configuration

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "licter": {
      "command": "python",
      "args": ["C:/Users/walid/Desktop/DEV/EugeniaSchool/LICTER/licter-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop. You'll see "LICTER Brand Intelligence" in the tools panel.

## Available Tools (8)

| Tool | Description |
|---|---|
| `get_brand_kpis` | KPIs: SoV, sentiment, NPS, Gravity Score |
| `search_mentions` | Search verbatims by keyword across all sources |
| `get_crisis_alerts` | Active crisis alerts with severity and timeline |
| `compare_brands` | Decathlon vs Intersport on any topic |
| `get_top_irritants` | Top customer pain points from reviews |
| `get_trending_topics` | Emerging trends detected in data |
| `get_influencers` | Top creators classified ambassador/detractor |
| `get_content_strategy_comparison` | AI analysis of content strategies |

## Example Conversations

> "Quel est le Gravity Score actuel de Decathlon ?"
> → Uses `get_brand_kpis` → "Le Gravity Score est de 10/10, crise active sur le velo defectueux."

> "Montre-moi les mentions SAV negatives"
> → Uses `search_mentions("SAV", brand="decathlon")` → returns top 20 verbatims

> "Compare Decathlon et Intersport sur le prix"
> → Uses `compare_brands("prix")` → SoV, sentiment, radar data

## Architecture

```
Claude Desktop / ChatGPT
        |
    MCP Protocol
        |
  licter-mcp/server.py
        |
  LICTER API (localhost:8000 or Workers)
        |
  SQLite / D1 (8300+ records, 13 sources)
```

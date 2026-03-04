"""
Smart Finances MCP Server – HTTP/SSE transport.

Run with:
    python -m mcp_server.server

Or expose the ASGI app directly (e.g. via uvicorn):
    uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001

Endpoints:
    GET  /sse        – SSE channel (agents connect here)
    POST /messages/  – Tool invocation messages

Authentication flow:
    1. Agent calls the `login` tool with email + password.
    2. Server authenticates via Supabase and returns a session_token.
    3. Agent passes that session_token to every subsequent tool call.
    4. Agent calls `logout` when done to invalidate the session.
"""

import os

from mcp.server.fastmcp import FastMCP

# ── tool imports ────────────────────────────────────────────────────────────
from mcp_server.tools.auth_tools import login, logout
from mcp_server.tools.user_tools import get_user_profile
from mcp_server.tools.account_tools import get_account, get_accounts
from mcp_server.tools.category_tools import get_categories, get_category
from mcp_server.tools.concept_tools import get_concept, get_concepts
from mcp_server.tools.tag_tools import get_tag, get_tags
from mcp_server.tools.transaction_tools import (
    get_recent_transactions,
    get_transaction,
    search_transactions,
)
from mcp_server.tools.reporting_tools import (
    get_balance,
    get_balance_accounts,
    get_balance_history,
    get_cashflow_history,
    get_cashflow_summary,
    get_categories_summary,
    get_period_comparison,
)

# ── server setup ─────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Smart Finances",
    instructions=(
        "This is the Smart Finances MCP server. "
        "You must call the 'login' tool first and pass the returned "
        "session_token to every other tool. "
        "Call 'logout' when finished."
    ),
)

# ── auth ─────────────────────────────────────────────────────────────────────
mcp.tool()(login)
mcp.tool()(logout)

# ── user ─────────────────────────────────────────────────────────────────────
mcp.tool()(get_user_profile)

# ── accounts ─────────────────────────────────────────────────────────────────
mcp.tool()(get_accounts)
mcp.tool()(get_account)

# ── categories ───────────────────────────────────────────────────────────────
mcp.tool()(get_categories)
mcp.tool()(get_category)

# ── concepts ─────────────────────────────────────────────────────────────────
mcp.tool()(get_concepts)
mcp.tool()(get_concept)

# ── tags ─────────────────────────────────────────────────────────────────────
mcp.tool()(get_tags)
mcp.tool()(get_tag)

# ── transactions ─────────────────────────────────────────────────────────────
mcp.tool()(search_transactions)
mcp.tool()(get_recent_transactions)
mcp.tool()(get_transaction)

# ── reporting ────────────────────────────────────────────────────────────────
mcp.tool()(get_categories_summary)
mcp.tool()(get_cashflow_summary)
mcp.tool()(get_period_comparison)
mcp.tool()(get_cashflow_history)
mcp.tool()(get_balance)
mcp.tool()(get_balance_accounts)
mcp.tool()(get_balance_history)

# ── ASGI app (for uvicorn / Vercel / any ASGI host) ──────────────────────────
app = mcp.sse_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)

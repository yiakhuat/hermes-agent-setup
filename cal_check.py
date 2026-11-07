import asyncio, json, os, sys

os.environ.setdefault("ICLOUD_EMAIL", "yiakhuat@icloud.com")
os.environ.setdefault("ICLOUD_PASSWORD", "zrmn-mkmu-sbty-bwle")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="/root/hermes-venv/bin/python3",
        args=["/root/icloud_calendar_mcp.py"],
        env=dict(os.environ),
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            res = await session.call_tool("list_events", {"days": 1})
            for c in res.content:
                print(c.text)

asyncio.run(main())

import asyncio, os
from datetime import datetime, timedelta
import caldav
from icalendar import Calendar, Event
import uuid
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("icloud-calendar")

def get_client():
    return caldav.DAVClient(
        url="https://caldav.icloud.com",
        username=os.environ["ICLOUD_EMAIL"],
        password=os.environ["ICLOUD_PASSWORD"],
        timeout=20
    )

def fetch_events(cal_filter, days):
    client = get_client()
    principal = client.principal()
    calendars = principal.calendars()
    results = []
    start = datetime.now()
    end = start + timedelta(days=days)
    for cal in calendars:
        try:
            cal_name = cal.get_display_name()
            if cal_name == "Reminders":
                continue
            if cal_filter and cal_filter.lower() not in cal_name.lower():
                continue
            events = cal.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    v = event.vobject_instance.vevent
                    summary = str(v.summary.value) if hasattr(v, 'summary') else 'No title'
                    dtstart = str(v.dtstart.value) if hasattr(v, 'dtstart') else 'Unknown date'
                    dtend = str(v.dtend.value) if hasattr(v, 'dtend') else ''
                    uid = str(v.uid.value) if hasattr(v, 'uid') else ''
                    results.append(f"- {summary} | {dtstart} to {dtend} | {cal_name} | UID:{uid}")
                except:
                    pass
        except Exception as e:
            pass
    return "\n".join(results) if results else "No events found"

def create_event(cal_name, summary, start_str, end_str, description=""):
    client = get_client()
    principal = client.principal()
    calendars = principal.calendars()
    target_cal = None
    for cal in calendars:
        if cal_name.lower() in cal.get_display_name().lower():
            target_cal = cal
            break
    if not target_cal:
        return f"Calendar '{cal_name}' not found"
    cal_obj = Calendar()
    cal_obj.add('prodid', '-//Hermes Agent//EN')
    cal_obj.add('version', '2.0')
    event = Event()
    event.add('summary', summary)
    event.add('dtstart', datetime.fromisoformat(start_str))
    event.add('dtend', datetime.fromisoformat(end_str))
    event.add('uid', str(uuid.uuid4()))
    if description:
        event.add('description', description)
    cal_obj.add_component(event)
    target_cal.save_event(cal_obj.to_ical().decode('utf-8'))
    return f"✅ Event '{summary}' created in {cal_name} calendar on {start_str}"

def update_event(uid, new_summary=None, new_start=None, new_end=None, new_description=None):
    client = get_client()
    principal = client.principal()
    calendars = principal.calendars()
    for cal in calendars:
        try:
            events = cal.events()
            for event in events:
                v = event.vobject_instance.vevent
                if hasattr(v, 'uid') and str(v.uid.value) == uid:
                    if new_summary:
                        v.summary.value = new_summary
                    if new_start:
                        v.dtstart.value = datetime.fromisoformat(new_start)
                    if new_end:
                        v.dtend.value = datetime.fromisoformat(new_end)
                    if new_description:
                        if hasattr(v, 'description'):
                            v.description.value = new_description
                    event.save()
                    return f"✅ Event updated successfully"
        except:
            pass
    return "❌ Event not found with that UID"

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="list_events",
            description="List upcoming iCloud calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 7},
                    "calendar": {"type": "string", "default": ""}
                }
            }
        ),
        types.Tool(
            name="create_event",
            description="Create a new event in iCloud calendar",
            inputSchema={
                "type": "object",
                "required": ["calendar", "summary", "start", "end"],
                "properties": {
                    "calendar": {"type": "string", "description": "Calendar name e.g. Home, Work, Family"},
                    "summary": {"type": "string", "description": "Event title"},
                    "start": {"type": "string", "description": "Start datetime in ISO format e.g. 2026-05-10T09:00:00"},
                    "end": {"type": "string", "description": "End datetime in ISO format e.g. 2026-05-10T10:00:00"},
                    "description": {"type": "string", "default": ""}
                }
            }
        ),
        types.Tool(
            name="update_event",
            description="Update an existing iCloud calendar event by UID",
            inputSchema={
                "type": "object",
                "required": ["uid"],
                "properties": {
                    "uid": {"type": "string", "description": "Event UID from list_events"},
                    "summary": {"type": "string"},
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    loop = asyncio.get_event_loop()
    if name == "list_events":
        text = await asyncio.wait_for(
            loop.run_in_executor(None, fetch_events,
                arguments.get("calendar", ""),
                arguments.get("days", 7)),
            timeout=50)
    elif name == "create_event":
        text = await asyncio.wait_for(
            loop.run_in_executor(None, create_event,
                arguments["calendar"],
                arguments["summary"],
                arguments["start"],
                arguments["end"],
                arguments.get("description", "")),
            timeout=50)
    elif name == "update_event":
        text = await asyncio.wait_for(
            loop.run_in_executor(None, update_event,
                arguments["uid"],
                arguments.get("summary"),
                arguments.get("start"),
                arguments.get("end"),
                arguments.get("description")),
            timeout=50)
    else:
        text = "Unknown tool"
    return [types.TextContent(type="text", text=text)]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())

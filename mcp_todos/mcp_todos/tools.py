"""MCP tool definitions for MyAIAssistant todos."""

TOOLS = [
    {
        "name": "create_todo",
        "description": "Create a todo in the MyAIAssistant backend. Title is required; other fields are optional.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the todo (required)",
                    "minLength": 1,
                    "maxLength": 255,
                },
                "description": {"type": "string", "description": "Optional description"},
                "status": {
                    "type": "string",
                    "description": "Status: Open, Started, Completed, Cancelled",
                    "enum": ["Open", "Started", "Completed", "Cancelled"],
                },
                "urgency": {
                    "type": "string",
                    "description": "Urgency: Urgent, Not Urgent",
                    "enum": ["Urgent", "Not Urgent"],
                },
                "importance": {
                    "type": "string",
                    "description": "Importance: Important, Not Important",
                    "enum": ["Important", "Not Important"],
                },
                "category": {"type": "string", "description": "Category for grouping", "maxLength": 100},
                "tags": {"type": "string", "description": "Comma-separated tags", "maxLength": 500},
                "project_id": {"type": "integer", "description": "Related project ID"},
                "due_date": {"type": "string", "description": "ISO datetime string for due date"},
                "source_type": {"type": "string", "description": "Source type e.g. meeting", "maxLength": 50},
                "source_id": {"type": "integer", "description": "Source reference ID"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "search_todos",
        "description": "Search or list todos with optional filters (search substring, status, category, limit, skip).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Substring to match in title or description", "maxLength": 200},
                "status": {"type": "string", "description": "Filter by status"},
                "category": {"type": "string", "description": "Filter by category"},
                "limit": {"type": "integer", "description": "Max number of results", "default": 100},
                "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
            },
            "required": [],
        },
    },
    {
        "name": "get_todo",
        "description": "Get a single todo by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "Todo ID"},
            },
            "required": ["todo_id"],
        },
    },
    {
        "name": "update_todo",
        "description": "Update an existing todo by ID. Only provided fields are updated.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "Todo ID to update"},
                "title": {"type": "string", "minLength": 1, "maxLength": 255},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["Open", "Started", "Completed", "Cancelled"]},
                "urgency": {"type": "string", "enum": ["Urgent", "Not Urgent"]},
                "importance": {"type": "string", "enum": ["Important", "Not Important"]},
                "category": {"type": "string", "maxLength": 100},
                "tags": {"type": "string", "maxLength": 500},
                "project_id": {"type": "integer"},
                "due_date": {"type": "string"},
                "source_type": {"type": "string", "maxLength": 50},
                "source_id": {"type": "integer"},
            },
            "required": ["todo_id"],
        },
    },
    {
        "name": "delete_todo",
        "description": "Delete a todo by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "Todo ID to delete"},
            },
            "required": ["todo_id"],
        },
    },
]

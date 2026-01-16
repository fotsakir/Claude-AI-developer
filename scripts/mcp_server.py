#!/usr/bin/env python3
"""
CodeHero MCP Server
Provides tools for Claude to manage projects and tickets via the CodeHero API.
"""

import json
import sys
import os
import mysql.connector
from datetime import datetime
from typing import Any, Dict, List, Optional

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'claude_user',
    'password': 'claudepass123',
    'database': 'claude_knowledge'
}

def get_db_connection():
    """Get a database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def log_error(msg: str):
    """Log error to stderr."""
    sys.stderr.write(f"[CodeHero MCP] ERROR: {msg}\n")
    sys.stderr.flush()

def log_info(msg: str):
    """Log info to stderr."""
    sys.stderr.write(f"[CodeHero MCP] {msg}\n")
    sys.stderr.flush()

# Tool definitions
TOOLS = [
    {
        "name": "codehero_list_projects",
        "description": "List all projects in CodeHero. Returns project names, IDs, types, and status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status (active, completed, all). Default: active",
                    "enum": ["active", "completed", "all"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of projects to return. Default: 20"
                }
            },
            "required": []
        }
    },
    {
        "name": "codehero_get_project",
        "description": "Get detailed information about a specific project including its tickets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "The project ID"
                },
                "project_name": {
                    "type": "string",
                    "description": "The project name (alternative to ID)"
                }
            },
            "required": []
        }
    },
    {
        "name": "codehero_create_project",
        "description": "Create a new project in CodeHero. Projects organize work and contain tickets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name (required)"
                },
                "description": {
                    "type": "string",
                    "description": "Project description"
                },
                "project_type": {
                    "type": "string",
                    "description": "Type of project: web, app, api, cli, library, other",
                    "enum": ["web", "app", "api", "cli", "library", "other"]
                },
                "tech_stack": {
                    "type": "string",
                    "description": "Technology stack: php, python, node, java, dotnet, other"
                },
                "web_path": {
                    "type": "string",
                    "description": "Path for web files (e.g., /var/www/html/myproject)"
                },
                "app_path": {
                    "type": "string",
                    "description": "Path for app/backend files"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "codehero_list_tickets",
        "description": "List tickets for a project. Shows ticket numbers, titles, status, and priority.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "The project ID (required)"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status: open, in_progress, awaiting_input, completed, closed, all",
                    "enum": ["open", "in_progress", "awaiting_input", "completed", "closed", "all"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of tickets to return. Default: 20"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "codehero_get_ticket",
        "description": "Get detailed information about a specific ticket including description and conversation history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "The ticket ID"
                },
                "ticket_number": {
                    "type": "string",
                    "description": "The ticket number (e.g., 'PROJ-0001')"
                }
            },
            "required": []
        }
    },
    {
        "name": "codehero_create_ticket",
        "description": "Create a new ticket in a project. Tickets represent tasks for Claude to work on.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "The project ID (required)"
                },
                "title": {
                    "type": "string",
                    "description": "Ticket title (required)"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the task"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority: low, medium, high, critical",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "auto_start": {
                    "type": "boolean",
                    "description": "Automatically start processing. Default: true"
                }
            },
            "required": ["project_id", "title"]
        }
    },
    {
        "name": "codehero_update_ticket",
        "description": "Update an existing ticket (status, priority, add reply).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "The ticket ID (required)"
                },
                "status": {
                    "type": "string",
                    "description": "New status",
                    "enum": ["open", "in_progress", "awaiting_input", "completed", "closed"]
                },
                "priority": {
                    "type": "string",
                    "description": "New priority",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "reply": {
                    "type": "string",
                    "description": "Add a user reply to the ticket conversation"
                }
            },
            "required": ["ticket_id"]
        }
    },
    {
        "name": "codehero_dashboard_stats",
        "description": "Get dashboard statistics: project counts, ticket counts, recent activity.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def handle_list_projects(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all projects."""
    status = args.get('status', 'active')
    limit = args.get('limit', 20)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if status == 'all':
            query = """
                SELECT id, name, description, project_type, tech_stack, status,
                       created_at, code,
                       (SELECT COUNT(*) FROM tickets WHERE project_id = projects.id) as ticket_count,
                       (SELECT COUNT(*) FROM tickets WHERE project_id = projects.id AND status IN ('open', 'in_progress')) as open_tickets
                FROM projects
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
        else:
            query = """
                SELECT id, name, description, project_type, tech_stack, status,
                       created_at, code,
                       (SELECT COUNT(*) FROM tickets WHERE project_id = projects.id) as ticket_count,
                       (SELECT COUNT(*) FROM tickets WHERE project_id = projects.id AND status IN ('open', 'in_progress')) as open_tickets
                FROM projects
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (status, limit))

        projects = cursor.fetchall()

        # Convert datetime to string
        for p in projects:
            if p.get('created_at'):
                p['created_at'] = p['created_at'].isoformat()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"projects": projects, "count": len(projects)}, indent=2)
                }
            ]
        }
    finally:
        cursor.close()
        conn.close()

def handle_get_project(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get project details."""
    project_id = args.get('project_id')
    project_name = args.get('project_name')

    if not project_id and not project_name:
        return {"content": [{"type": "text", "text": "Error: Either project_id or project_name is required"}]}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if project_id:
            cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        else:
            cursor.execute("SELECT * FROM projects WHERE name = %s", (project_name,))

        project = cursor.fetchone()

        if not project:
            return {"content": [{"type": "text", "text": f"Error: Project not found"}]}

        # Get recent tickets
        cursor.execute("""
            SELECT id, ticket_number, title, status, priority, created_at
            FROM tickets
            WHERE project_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (project['id'],))
        tickets = cursor.fetchall()

        # Convert datetime
        if project.get('created_at'):
            project['created_at'] = project['created_at'].isoformat()
        if project.get('updated_at'):
            project['updated_at'] = project['updated_at'].isoformat()
        for t in tickets:
            if t.get('created_at'):
                t['created_at'] = t['created_at'].isoformat()

        result = {
            "project": project,
            "recent_tickets": tickets
        }

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    finally:
        cursor.close()
        conn.close()

def handle_create_project(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new project."""
    name = args.get('name')
    if not name:
        return {"content": [{"type": "text", "text": "Error: name is required"}]}

    description = args.get('description', '')
    project_type = args.get('project_type', 'web')
    tech_stack = args.get('tech_stack', 'php')
    web_path = args.get('web_path', '')
    app_path = args.get('app_path', '')

    # Generate code from name
    code = ''.join(c.upper() for c in name if c.isalnum())[:4]
    if not code:
        code = 'PROJ'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if project name exists
        cursor.execute("SELECT id FROM projects WHERE name = %s", (name,))
        if cursor.fetchone():
            return {"content": [{"type": "text", "text": f"Error: Project '{name}' already exists"}]}

        # Check code uniqueness and modify if needed
        cursor.execute("SELECT code FROM projects WHERE code = %s", (code,))
        if cursor.fetchone():
            # Add number to make unique
            for i in range(1, 100):
                new_code = f"{code[:3]}{i}"
                cursor.execute("SELECT code FROM projects WHERE code = %s", (new_code,))
                if not cursor.fetchone():
                    code = new_code
                    break

        cursor.execute("""
            INSERT INTO projects (name, description, project_type, tech_stack, web_path, app_path, code, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        """, (name, description, project_type, tech_stack, web_path, app_path, code))

        conn.commit()
        project_id = cursor.lastrowid

        result = {
            "success": True,
            "project_id": project_id,
            "name": name,
            "code": code,
            "message": f"Project '{name}' created successfully with code '{code}'"
        }

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error creating project: {str(e)}"}]}
    finally:
        cursor.close()
        conn.close()

def handle_list_tickets(args: Dict[str, Any]) -> Dict[str, Any]:
    """List tickets for a project."""
    project_id = args.get('project_id')
    if not project_id:
        return {"content": [{"type": "text", "text": "Error: project_id is required"}]}

    status = args.get('status', 'all')
    limit = args.get('limit', 20)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if status == 'all':
            cursor.execute("""
                SELECT id, ticket_number, title, status, priority, created_at, updated_at
                FROM tickets
                WHERE project_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (project_id, limit))
        else:
            cursor.execute("""
                SELECT id, ticket_number, title, status, priority, created_at, updated_at
                FROM tickets
                WHERE project_id = %s AND status = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (project_id, status, limit))

        tickets = cursor.fetchall()

        for t in tickets:
            if t.get('created_at'):
                t['created_at'] = t['created_at'].isoformat()
            if t.get('updated_at'):
                t['updated_at'] = t['updated_at'].isoformat()

        return {"content": [{"type": "text", "text": json.dumps({"tickets": tickets, "count": len(tickets)}, indent=2)}]}
    finally:
        cursor.close()
        conn.close()

def handle_get_ticket(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get ticket details."""
    ticket_id = args.get('ticket_id')
    ticket_number = args.get('ticket_number')

    if not ticket_id and not ticket_number:
        return {"content": [{"type": "text", "text": "Error: Either ticket_id or ticket_number is required"}]}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if ticket_id:
            cursor.execute("""
                SELECT t.*, p.name as project_name, p.code
                FROM tickets t
                JOIN projects p ON t.project_id = p.id
                WHERE t.id = %s
            """, (ticket_id,))
        else:
            cursor.execute("""
                SELECT t.*, p.name as project_name, p.code
                FROM tickets t
                JOIN projects p ON t.project_id = p.id
                WHERE t.ticket_number = %s
            """, (ticket_number,))

        ticket = cursor.fetchone()

        if not ticket:
            return {"content": [{"type": "text", "text": "Error: Ticket not found"}]}

        # Get conversation
        cursor.execute("""
            SELECT role, content, created_at
            FROM ticket_messages
            WHERE ticket_id = %s
            ORDER BY created_at ASC
        """, (ticket['id'],))
        messages = cursor.fetchall()

        # Convert datetime
        if ticket.get('created_at'):
            ticket['created_at'] = ticket['created_at'].isoformat()
        if ticket.get('updated_at'):
            ticket['updated_at'] = ticket['updated_at'].isoformat()
        for m in messages:
            if m.get('created_at'):
                m['created_at'] = m['created_at'].isoformat()

        result = {
            "ticket": ticket,
            "conversation": messages
        }

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    finally:
        cursor.close()
        conn.close()

def handle_create_ticket(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new ticket."""
    project_id = args.get('project_id')
    title = args.get('title')

    if not project_id:
        return {"content": [{"type": "text", "text": "Error: project_id is required"}]}
    if not title:
        return {"content": [{"type": "text", "text": "Error: title is required"}]}

    description = args.get('description', '')
    priority = args.get('priority', 'medium')
    auto_start = args.get('auto_start', True)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get project code and next ticket number
        cursor.execute("SELECT id, code FROM projects WHERE id = %s", (project_id,))
        project = cursor.fetchone()

        if not project:
            return {"content": [{"type": "text", "text": f"Error: Project ID {project_id} not found"}]}

        code = project['code']

        # Get next ticket number
        cursor.execute("""
            SELECT ticket_number FROM tickets
            WHERE project_id = %s
            ORDER BY id DESC LIMIT 1
        """, (project_id,))
        last_ticket = cursor.fetchone()

        if last_ticket:
            # Extract number from ticket_number like "PROJ-0001"
            try:
                last_num = int(last_ticket['ticket_number'].split('-')[1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1

        ticket_number = f"{code}-{next_num:04d}"
        status = 'open' if auto_start else 'open'

        cursor.execute("""
            INSERT INTO tickets (project_id, ticket_number, title, description, status, priority)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (project_id, ticket_number, title, description, status, priority))

        conn.commit()
        ticket_id = cursor.lastrowid

        # Add initial message if description provided
        if description:
            cursor.execute("""
                INSERT INTO ticket_messages (ticket_id, role, content)
                VALUES (%s, 'user', %s)
            """, (ticket_id, description))
            conn.commit()

        result = {
            "success": True,
            "ticket_id": ticket_id,
            "ticket_number": ticket_number,
            "title": title,
            "status": status,
            "message": f"Ticket {ticket_number} created successfully"
        }

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error creating ticket: {str(e)}"}]}
    finally:
        cursor.close()
        conn.close()

def handle_update_ticket(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update a ticket."""
    ticket_id = args.get('ticket_id')
    if not ticket_id:
        return {"content": [{"type": "text", "text": "Error: ticket_id is required"}]}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check ticket exists
        cursor.execute("SELECT id, ticket_number FROM tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()

        if not ticket:
            return {"content": [{"type": "text", "text": f"Error: Ticket ID {ticket_id} not found"}]}

        updates = []
        params = []

        if 'status' in args:
            updates.append("status = %s")
            params.append(args['status'])

        if 'priority' in args:
            updates.append("priority = %s")
            params.append(args['priority'])

        if updates:
            updates.append("updated_at = NOW()")
            params.append(ticket_id)
            cursor.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE id = %s", params)

        # Add reply if provided
        if 'reply' in args and args['reply']:
            cursor.execute("""
                INSERT INTO ticket_messages (ticket_id, role, content)
                VALUES (%s, 'user', %s)
            """, (ticket_id, args['reply']))
            # Set ticket to open so daemon picks it up
            cursor.execute("UPDATE tickets SET status = 'open', updated_at = NOW() WHERE id = %s", (ticket_id,))

        conn.commit()

        result = {
            "success": True,
            "ticket_id": ticket_id,
            "ticket_number": ticket['ticket_number'],
            "message": f"Ticket {ticket['ticket_number']} updated successfully"
        }

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error updating ticket: {str(e)}"}]}
    finally:
        cursor.close()
        conn.close()

def handle_dashboard_stats(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get dashboard statistics."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Project counts
        cursor.execute("SELECT COUNT(*) as total FROM projects")
        total_projects = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as active FROM projects WHERE status = 'active'")
        active_projects = cursor.fetchone()['active']

        # Ticket counts
        cursor.execute("SELECT COUNT(*) as total FROM tickets")
        total_tickets = cursor.fetchone()['total']

        cursor.execute("SELECT status, COUNT(*) as count FROM tickets GROUP BY status")
        ticket_stats = {row['status']: row['count'] for row in cursor.fetchall()}

        # Recent activity
        cursor.execute("""
            SELECT t.ticket_number, t.title, t.status, t.updated_at, p.name as project_name
            FROM tickets t
            JOIN projects p ON t.project_id = p.id
            ORDER BY t.updated_at DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()

        for r in recent:
            if r.get('updated_at'):
                r['updated_at'] = r['updated_at'].isoformat()

        result = {
            "projects": {
                "total": total_projects,
                "active": active_projects
            },
            "tickets": {
                "total": total_tickets,
                "by_status": ticket_stats
            },
            "recent_activity": recent
        }

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
    finally:
        cursor.close()
        conn.close()

# Tool handlers mapping
TOOL_HANDLERS = {
    "codehero_list_projects": handle_list_projects,
    "codehero_get_project": handle_get_project,
    "codehero_create_project": handle_create_project,
    "codehero_list_tickets": handle_list_tickets,
    "codehero_get_ticket": handle_get_ticket,
    "codehero_create_ticket": handle_create_ticket,
    "codehero_update_ticket": handle_update_ticket,
    "codehero_dashboard_stats": handle_dashboard_stats,
}

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming JSON-RPC request."""
    method = request.get('method', '')
    request_id = request.get('id')
    params = request.get('params', {})

    if method == 'initialize':
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "codehero-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == 'notifications/initialized':
        return None  # No response needed

    elif method == 'tools/list':
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == 'tools/call':
        tool_name = params.get('name')
        tool_args = params.get('arguments', {})

        if tool_name in TOOL_HANDLERS:
            try:
                result = TOOL_HANDLERS[tool_name](tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            except Exception as e:
                log_error(f"Tool {tool_name} error: {str(e)}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

    elif method == 'ping':
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {}
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

def main():
    """Main entry point - stdio JSON-RPC server."""
    log_info("Starting CodeHero MCP Server...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = handle_request(request)

            if response is not None:
                sys.stdout.write(json.dumps(response) + '\n')
                sys.stdout.flush()

        except json.JSONDecodeError as e:
            log_error(f"JSON decode error: {e}")
        except Exception as e:
            log_error(f"Error: {e}")

if __name__ == '__main__':
    main()

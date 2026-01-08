#!/usr/bin/env python3
"""
Claude Code Daemon v3 - Multi-worker with project isolation
- One worker per project (parallel between projects)
- Sequential execution within each project
- Runs as claude-worker user
- Restricted to project directories
"""

import subprocess
import time
import json
import os
import sys
import signal
import smtplib
import threading
import urllib.request
import urllib.error
import shutil
import zipfile
import tempfile
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from mysql.connector import pooling

BACKUP_DIR = "/var/backups/fotios-claude"
MAX_BACKUPS = 30

# Web app URL for broadcasting messages
WEB_APP_URL = "http://127.0.0.1:5000"

CONFIG_FILE = "/etc/fotios-claude/system.conf"
PID_FILE = "/var/run/fotios-claude/daemon.pid"
LOG_FILE = "/var/log/fotios-claude/daemon.log"
GLOBAL_CONTEXT_FILE = "/etc/fotios-claude/global-context.md"
STUCK_TIMEOUT_MINUTES = 30
POLL_INTERVAL = 3
MAX_PARALLEL_PROJECTS = 3

class ProjectWorker(threading.Thread):
    """Worker thread for a specific project"""

    def __init__(self, daemon, project_id, project_name, work_path, global_context=""):
        super().__init__(daemon=True)
        self.daemon_ref = daemon
        self.project_id = project_id
        self.project_name = project_name
        self.work_path = work_path
        self.global_context = global_context
        self.running = True
        self.current_ticket_id = None
        self.current_session_id = None
        self.last_activity = None
        # Token tracking
        self.session_start_time = None
        self.session_input_tokens = 0
        self.session_output_tokens = 0
        self.session_cache_read_tokens = 0
        self.session_cache_creation_tokens = 0
        self.session_api_calls = 0
        
    def log(self, message, level="INFO"):
        self.daemon_ref.log(f"[{self.project_name}] {message}", level)
    
    def get_db(self):
        return self.daemon_ref.get_db()
    
    def broadcast_message(self, msg_data):
        """Send message to web app for WebSocket broadcast"""
        try:
            data = json.dumps({
                'type': 'message',
                'ticket_id': self.current_ticket_id,
                'message': msg_data
            }).encode('utf-8')
            req = urllib.request.Request(
                f"{WEB_APP_URL}/api/internal/broadcast",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=2)
        except:
            pass  # Don't let broadcast failures affect the daemon

    def save_message(self, role, content, tool_name=None, tool_input=None, tokens=0):
        if not self.current_ticket_id:
            return
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_messages
                (ticket_id, session_id, role, content, tool_name, tool_input, tokens_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                self.current_ticket_id,
                self.current_session_id,
                role,
                content[:50000] if content else None,
                tool_name,
                json.dumps(tool_input) if tool_input else None,
                tokens
            ))
            msg_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            self.last_activity = datetime.now()

            # Broadcast to web app for real-time updates
            self.broadcast_message({
                'id': msg_id,
                'ticket_id': self.current_ticket_id,
                'role': role,
                'content': content[:50000] if content else None,
                'tool_name': tool_name,
                'tool_input': json.dumps(tool_input) if tool_input else None,
                'created_at': datetime.now().isoformat() + 'Z'
            })
        except Exception as e:
            self.log(f"Error saving message: {e}", "ERROR")
    
    def save_log(self, log_type, message):
        if not self.current_session_id:
            return
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execution_logs (session_id, log_type, message, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (self.current_session_id, log_type, message[:10000]))
            conn.commit()
            cursor.close()
            conn.close()
        except: pass
    
    def get_next_ticket(self):
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.*, p.web_path, p.app_path, p.name as project_name, p.code as project_code,
                       p.project_type, p.tech_stack, p.context as project_context, t.context as ticket_context,
                       p.db_name, p.db_user, p.db_password, p.db_host
                FROM tickets t
                JOIN projects p ON t.project_id = p.id
                WHERE t.project_id = %s AND t.status IN ('open', 'new', 'pending')
                ORDER BY
                    CASE t.priority
                        WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3 WHEN 'low' THEN 4
                    END,
                    t.created_at ASC
                LIMIT 1
            """, (self.project_id,))
            ticket = cursor.fetchone()
            cursor.close()
            conn.close()
            return ticket
        except Exception as e:
            self.log(f"Error getting ticket: {e}", "ERROR")
            return None
    
    def get_conversation_history(self, ticket_id):
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT role, content, tool_name, tool_input FROM conversation_messages
                WHERE ticket_id = %s ORDER BY created_at ASC
            """, (ticket_id,))
            messages = cursor.fetchall()
            cursor.close()
            conn.close()
            return messages
        except:
            return []
    
    def get_pending_user_messages(self, ticket_id):
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM user_messages 
                WHERE ticket_id = %s AND processed = FALSE
                ORDER BY created_at ASC
            """, (ticket_id,))
            messages = cursor.fetchall()
            if messages:
                ids = [m['id'] for m in messages]
                cursor.execute(f"UPDATE user_messages SET processed = TRUE WHERE id IN ({','.join(map(str, ids))})")
                conn.commit()
            cursor.close()
            conn.close()
            return messages
        except:
            return []
    
    def update_ticket(self, ticket_id, status, result=None):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            if status == 'done':
                # Set to awaiting_input instead of done - user must respond or close
                cursor.execute("""
                    UPDATE tickets SET status = 'awaiting_input', result_summary = %s,
                    review_deadline = DATE_ADD(NOW(), INTERVAL 7 DAY), updated_at = NOW()
                    WHERE id = %s
                """, (result[:1000] if result else None, ticket_id))
            else:
                cursor.execute("""
                    UPDATE tickets SET status = %s, result_summary = %s, updated_at = NOW()
                    WHERE id = %s
                """, (status, result[:1000] if result else None, ticket_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.log(f"Error updating ticket: {e}", "ERROR")

    def create_backup(self, ticket_id):
        """Create automatic backup before processing ticket"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.* FROM projects p
                JOIN tickets t ON t.project_id = p.id
                WHERE t.id = %s
            """, (ticket_id,))
            project = cursor.fetchone()
            cursor.close()
            conn.close()

            if not project:
                self.log("Could not find project for backup", "WARNING")
                return

            project_code = project['code']
            backup_subdir = os.path.join(BACKUP_DIR, project_code)
            os.makedirs(backup_subdir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{project_code}_{timestamp}_auto.zip"
            backup_path = os.path.join(backup_subdir, backup_name)

            temp_dir = tempfile.mkdtemp()
            temp_backup = os.path.join(temp_dir, 'backup')
            os.makedirs(temp_backup)

            try:
                # Copy web folder
                if project.get('web_path') and os.path.exists(project['web_path']):
                    shutil.copytree(project['web_path'], os.path.join(temp_backup, 'web'), dirs_exist_ok=True)

                # Copy app folder
                if project.get('app_path') and os.path.exists(project['app_path']):
                    shutil.copytree(project['app_path'], os.path.join(temp_backup, 'app'), dirs_exist_ok=True)

                # Export database
                if project.get('db_name') and project.get('db_user') and project.get('db_password'):
                    db_dir = os.path.join(temp_backup, 'database')
                    os.makedirs(db_dir, exist_ok=True)

                    db_host = project.get('db_host', 'localhost')
                    db_name = project['db_name']
                    db_user = project['db_user']
                    db_pass = project['db_password']

                    # Schema
                    schema_cmd = f"mysqldump -h {db_host} -u {db_user} -p'{db_pass}' --no-data {db_name} 2>/dev/null"
                    result = subprocess.run(schema_cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        with open(os.path.join(db_dir, 'schema.sql'), 'w') as f:
                            f.write(result.stdout)

                    # Data
                    data_cmd = f"mysqldump -h {db_host} -u {db_user} -p'{db_pass}' --no-create-info {db_name} 2>/dev/null"
                    result = subprocess.run(data_cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        with open(os.path.join(db_dir, 'data.sql'), 'w') as f:
                            f.write(result.stdout)

                # Create zip
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_backup):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, temp_backup)
                            zipf.write(file_path, arc_name)

                # Cleanup old backups
                backups = sorted(
                    [f for f in os.listdir(backup_subdir) if f.endswith('.zip')],
                    key=lambda x: os.path.getmtime(os.path.join(backup_subdir, x)),
                    reverse=True
                )
                for old_backup in backups[MAX_BACKUPS:]:
                    os.remove(os.path.join(backup_subdir, old_backup))

                self.log(f"Backup created: {backup_name}")
                self.save_log('info', f'Auto-backup created: {backup_name}')

            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            self.log(f"Backup error: {e}", "WARNING")

    def reset_token_tracking(self):
        """Reset token counters for a new session"""
        self.session_start_time = datetime.now()
        self.session_input_tokens = 0
        self.session_output_tokens = 0
        self.session_cache_read_tokens = 0
        self.session_cache_creation_tokens = 0
        self.session_api_calls = 0

    def save_usage_stats(self):
        """Save usage statistics to database"""
        if not self.current_ticket_id or not self.session_start_time:
            return

        try:
            # Calculate duration
            duration = int((datetime.now() - self.session_start_time).total_seconds())
            total_tokens = self.session_input_tokens + self.session_output_tokens

            conn = self.get_db()
            cursor = conn.cursor()

            # Insert usage record
            cursor.execute("""
                INSERT INTO usage_stats
                (ticket_id, project_id, session_id, input_tokens, output_tokens, total_tokens,
                 cache_read_tokens, cache_creation_tokens, duration_seconds, api_calls)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.current_ticket_id,
                self.project_id,
                self.current_session_id,
                self.session_input_tokens,
                self.session_output_tokens,
                total_tokens,
                self.session_cache_read_tokens,
                self.session_cache_creation_tokens,
                duration,
                self.session_api_calls
            ))

            # Update ticket totals
            cursor.execute("""
                UPDATE tickets
                SET total_tokens = total_tokens + %s,
                    total_duration_seconds = total_duration_seconds + %s
                WHERE id = %s
            """, (total_tokens, duration, self.current_ticket_id))

            # Update project totals
            cursor.execute("""
                UPDATE projects
                SET total_tokens = total_tokens + %s,
                    total_duration_seconds = total_duration_seconds + %s
                WHERE id = %s
            """, (total_tokens, duration, self.project_id))

            conn.commit()
            cursor.close()
            conn.close()

            self.log(f"Usage: {total_tokens:,} tokens, {duration}s, {self.session_api_calls} API calls")

        except Exception as e:
            self.log(f"Error saving usage stats: {e}", "ERROR")

    def create_session(self, ticket_id):
        try:
            self.reset_token_tracking()
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execution_sessions (ticket_id, status, started_at)
                VALUES (%s, 'running', NOW())
            """, (ticket_id,))
            session_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return session_id
        except Exception as e:
            self.log(f"Error creating session: {e}", "ERROR")
            return None
    
    def end_session(self, session_id, status, tokens=0):
        # Save usage stats before ending session
        self.save_usage_stats()

        try:
            # Use the total tokens we tracked
            total_tokens = self.session_input_tokens + self.session_output_tokens
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE execution_sessions SET status = %s, ended_at = NOW(), tokens_used = %s
                WHERE id = %s
            """, (status, total_tokens, session_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.log(f"Error ending session: {e}", "ERROR")
    
    def build_prompt(self, ticket, history):
        # Determine working paths
        paths_info = []
        if ticket.get('web_path'):
            paths_info.append(f"Web path: {ticket['web_path']}")
        if ticket.get('app_path'):
            paths_info.append(f"App path: {ticket['app_path']}")
        paths_str = "\n".join(paths_info) if paths_info else "No paths configured"

        # Build tech info
        tech_info = ""
        if ticket.get('tech_stack'):
            tech_info = f"\nTech Stack: {ticket.get('tech_stack')}"
        if ticket.get('project_type'):
            tech_info += f"\nProject Type: {ticket.get('project_type')}"

        # Global context (server environment, installed tools, etc)
        global_context_str = ""
        if self.global_context:
            global_context_str = f"""
=== SERVER ENVIRONMENT ===
{self.global_context}
==========================
"""

        # Project database credentials (auto-created)
        db_info = ""
        if ticket.get('db_name') and ticket.get('db_user'):
            db_info = f"""
=== PROJECT DATABASE ===
Host: {ticket.get('db_host', 'localhost')}
Database: {ticket['db_name']}
Username: {ticket['db_user']}
Password: {ticket['db_password']}
========================
"""

        # Project context (databases, APIs, credentials, etc)
        project_context = ""
        if ticket.get('project_context'):
            project_context = f"""
=== PROJECT CONTEXT ===
{ticket['project_context']}
=======================
"""
        
        # Ticket-specific context
        ticket_context = ""
        if ticket.get('ticket_context'):
            ticket_context = f"""
=== TICKET CONTEXT ===
{ticket['ticket_context']}
======================
"""
        
        # Allowed paths
        allowed_paths = []
        if ticket.get('web_path'): allowed_paths.append(ticket['web_path'])
        if ticket.get('app_path'): allowed_paths.append(ticket['app_path'])
        allowed_str = " and ".join(allowed_paths) if allowed_paths else "/var/www/projects"
        
        system = f"""You are working on project: {ticket['project_name']}
{paths_str}{tech_info}
{global_context_str}{db_info}{project_context}{ticket_context}
Ticket: {ticket['ticket_number']} - {ticket['title']}

IMPORTANT: You can ONLY create/modify files within: {allowed_str}
Do NOT attempt to modify system files or files outside these directories.

Description:
{ticket['description']}

Complete this task. When finished, say "TASK COMPLETED" with a summary."""
        
        prompt_parts = [system, "\n--- Conversation History ---\n"]
        
        for msg in history:
            if msg['role'] == 'user':
                prompt_parts.append(f"\nUser: {msg['content']}")
            elif msg['role'] == 'assistant':
                prompt_parts.append(f"\nAssistant: {msg['content']}")
            elif msg['role'] == 'tool_use':
                prompt_parts.append(f"\n[Used tool: {msg['tool_name']}]")
            elif msg['role'] == 'tool_result':
                result = msg['content'] or ''
                prompt_parts.append(f"\n[Result: {result[:200]}...]" if len(result) > 200 else f"\n[Result: {result}]")
        
        prompt_parts.append("\n\nContinue working on this task:")
        return '\n'.join(prompt_parts)
    
    def parse_claude_output(self, line):
        try:
            data = json.loads(line)
            msg_type = data.get('type', '')

            if msg_type == 'assistant':
                # Extract usage data from the message
                usage = data.get('message', {}).get('usage', {})
                if usage:
                    self.session_input_tokens += usage.get('input_tokens', 0)
                    self.session_output_tokens += usage.get('output_tokens', 0)
                    self.session_cache_read_tokens += usage.get('cache_read_input_tokens', 0)
                    self.session_cache_creation_tokens += usage.get('cache_creation_input_tokens', 0)
                    self.session_api_calls += 1

                content = ''
                for block in data.get('message', {}).get('content', []):
                    if block.get('type') == 'text':
                        content += block.get('text', '')
                    elif block.get('type') == 'tool_use':
                        self.save_message('tool_use', None,
                                        tool_name=block.get('name'),
                                        tool_input=block.get('input'))
                        self.save_log('output', f"🔧 Tool: {block.get('name')}")

                if content:
                    tokens = usage.get('output_tokens', 0)
                    self.save_message('assistant', content, tokens=tokens)
                    preview = content[:200] + '...' if len(content) > 200 else content
                    self.save_log('output', preview)

                    if 'TASK COMPLETED' in content.upper():
                        return 'completed'

            elif msg_type == 'result':
                result = data.get('result', '')
                if isinstance(result, dict):
                    result = json.dumps(result)
                self.save_message('tool_result', str(result)[:5000])

            elif msg_type == 'error':
                error = data.get('error', {}).get('message', 'Unknown error')
                self.save_message('system', f"Error: {error}")
                self.save_log('error', error)

        except json.JSONDecodeError:
            if line.strip():
                self.save_log('output', line.strip())

        return None
    
    def run_claude(self, ticket, prompt):
        """Run Claude Code within project directory"""
        
        # Determine working directory
        work_path = ticket.get('web_path') or ticket.get('app_path') or '/var/www/projects'
        work_path = os.path.abspath(work_path)
        
        # Create directories if needed
        if ticket.get('web_path'):
            os.makedirs(ticket['web_path'], exist_ok=True)
        if ticket.get('app_path'):
            os.makedirs(ticket['app_path'], exist_ok=True)
        
        cmd = [
            '/home/claude/.local/bin/claude',
            '--model', 'sonnet',
            '--verbose',
            '--output-format', 'stream-json',
            '--dangerously-skip-permissions',
            '-p', prompt
        ]
        try:
            # Run in project directory
            process = subprocess.Popen(
                cmd, 
                cwd=work_path,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, 
                bufsize=1
            )
            
            result = None
            while True:
                new_msgs = self.get_pending_user_messages(ticket['id'])
                for msg in new_msgs:
                    content = msg['content'].strip()
                    if content == '/skip':
                        process.terminate()
                        return 'skipped'
                    elif content == '/done':
                        process.terminate()
                        return 'completed'
                    elif content == '/stop':
                        process.terminate()
                        self.save_log('info', 'Stopped by user - waiting for new instructions')
                        return 'interrupted'
                
                if not self.running or not self.daemon_ref.running:
                    process.terminate()
                    return 'stopped'
                
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    result = self.parse_claude_output(line) or result
                    
                if self.last_activity:
                    stuck_time = (datetime.now() - self.last_activity).total_seconds()
                    if stuck_time > STUCK_TIMEOUT_MINUTES * 60:
                        self.log("STUCK detected", "ERROR")
                        self.daemon_ref.send_email(f"Stuck on {ticket['ticket_number']}", 
                                       f"Ticket: {ticket['title']}\nNo activity for {STUCK_TIMEOUT_MINUTES} minutes.")
                        process.terminate()
                        return 'stuck'
            
            return result if result else ('success' if process.returncode == 0 else 'failed')
            
        except Exception as e:
            self.log(f"Error running Claude: {e}", "ERROR")
            return 'failed'
    
    def process_ticket(self, ticket):
        self.current_ticket_id = ticket['id']
        self.current_session_id = self.create_session(ticket['id'])
        self.last_activity = datetime.now()

        self.log(f"Processing: {ticket['ticket_number']} - {ticket['title']}")

        # Create automatic backup before starting
        self.create_backup(ticket['id'])

        self.update_ticket(ticket['id'], 'in_progress')
        self.save_log('info', f"Starting: {ticket['ticket_number']}")

        history = self.get_conversation_history(ticket['id'])

        if not history:
            self.save_message('user', f"Task: {ticket['title']}\n\n{ticket['description']}")
            history = self.get_conversation_history(ticket['id'])

        # Loop to handle interruptions and pending messages
        while True:
            prompt = self.build_prompt(ticket, history)
            result = self.run_claude(ticket, prompt)

            if result == 'interrupted':
                # User sent /stop - check for new instructions
                time.sleep(1)  # Brief pause to allow message to be sent
                pending = self.get_pending_user_messages(ticket['id'])
                if pending:
                    # Add pending messages to conversation and continue
                    for msg in pending:
                        content = msg['content'].strip()
                        if not content.startswith('/'):  # Skip commands
                            self.save_message('user', content)
                            self.save_log('info', f'User message: {content[:100]}...' if len(content) > 100 else f'User message: {content}')
                    history = self.get_conversation_history(ticket['id'])
                    self.log(f"Continuing with user feedback...")
                    continue
                else:
                    # No messages yet, keep ticket open for user to add message
                    self.update_ticket(ticket['id'], 'open')
                    self.end_session(self.current_session_id, 'stopped')
                    self.log(f"⏸️ Stopped: {ticket['ticket_number']} - waiting for user input")
                    break

            elif result == 'completed':
                # Check for any pending messages before marking done
                pending = self.get_pending_user_messages(ticket['id'])
                if pending:
                    # User sent feedback - add to conversation and continue
                    for msg in pending:
                        content = msg['content'].strip()
                        if not content.startswith('/'):
                            self.save_message('user', content)
                            self.save_log('info', f'User message: {content[:100]}...' if len(content) > 100 else f'User message: {content}')
                    history = self.get_conversation_history(ticket['id'])
                    self.log(f"Processing user feedback before completing...")
                    continue

                self.update_ticket(ticket['id'], 'done', 'Completed successfully')
                self.end_session(self.current_session_id, 'completed')
                self.log(f"✅ Completed: {ticket['ticket_number']}")
                break

            elif result == 'skipped':
                self.update_ticket(ticket['id'], 'open')
                self.end_session(self.current_session_id, 'skipped')
                break

            elif result == 'stuck':
                self.update_ticket(ticket['id'], 'stuck')
                self.end_session(self.current_session_id, 'stuck')
                break

            elif result == 'stopped':
                self.update_ticket(ticket['id'], 'pending')
                self.end_session(self.current_session_id, 'stopped')
                break

            else:
                self.update_ticket(ticket['id'], 'failed', str(result))
                self.end_session(self.current_session_id, 'failed')
                self.log(f"❌ Failed: {ticket['ticket_number']}", "ERROR")
                break

        self.current_ticket_id = None
        self.current_session_id = None
    
    def run(self):
        self.log(f"Worker started")
        
        while self.running and self.daemon_ref.running:
            try:
                ticket = self.get_next_ticket()
                if ticket:
                    self.process_ticket(ticket)
                else:
                    time.sleep(POLL_INTERVAL)
                    ticket = self.get_next_ticket()
                    if not ticket:
                        self.log("No more tickets, worker stopping")
                        break
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                time.sleep(POLL_INTERVAL)
        
        self.log(f"Worker stopped")
    
    def stop(self):
        self.running = False


class ClaudeDaemon:
    """Main daemon - manages project workers"""

    def __init__(self):
        self.running = True
        self.config = self.load_config()
        self.db_pool = self.create_db_pool()
        self.workers = {}
        self.workers_lock = threading.Lock()
        self.max_parallel = int(self.config.get('MAX_PARALLEL_PROJECTS', MAX_PARALLEL_PROJECTS))
        self.global_context = self.load_global_context()

    def load_global_context(self):
        """Load global context that applies to all projects"""
        try:
            if os.path.exists(GLOBAL_CONTEXT_FILE):
                with open(GLOBAL_CONTEXT_FILE, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            self.log(f"Warning: Could not load global context: {e}", "WARNING")
        return ""
        
    def load_config(self):
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"').strip("'")
        return config
    
    def create_db_pool(self):
        return pooling.MySQLConnectionPool(
            host=self.config.get('DB_HOST', 'localhost'),
            user=self.config.get('DB_USER', 'claude_user'),
            password=self.config.get('DB_PASSWORD', ''),
            database=self.config.get('DB_NAME', 'claude_knowledge'),
            pool_name='daemon_pool',
            pool_size=10
        )
    
    def get_db(self):
        return self.db_pool.get_connection()
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'a') as f:
                f.write(log_line + "\n")
        except: pass
    
    def send_email(self, subject, body):
        if self.config.get('SMTP_ENABLED', 'false').lower() != 'true':
            return
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.get('SMTP_USER', '')
            msg['To'] = self.config.get('ALERT_EMAIL', '')
            msg['Subject'] = f"[Fotios Claude] {subject}"
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.get('SMTP_HOST', 'smtp.gmail.com'),
                                 int(self.config.get('SMTP_PORT', '587')))
            if self.config.get('SMTP_USE_TLS', 'true').lower() == 'true':
                server.starttls()
            server.login(self.config.get('SMTP_USER', ''), self.config.get('SMTP_PASSWORD', ''))
            server.send_message(msg)
            server.quit()
            self.log(f"Email sent: {subject}")
        except Exception as e:
            self.log(f"Email error: {e}", "ERROR")
    
    def get_projects_with_open_tickets(self):
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT p.id, p.name, p.code, COALESCE(p.web_path, p.app_path) as work_path,
                       (SELECT COUNT(*) FROM tickets WHERE project_id = p.id AND status IN ('open', 'new', 'pending')) as open_count
                FROM projects p
                JOIN tickets t ON t.project_id = p.id
                WHERE t.status IN ('open', 'new', 'pending')
                AND p.status = 'active'
                ORDER BY 
                    (SELECT MIN(CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END) 
                     FROM tickets WHERE project_id = p.id AND status IN ('open', 'new', 'pending')) ASC
            """)
            projects = cursor.fetchall()
            cursor.close()
            conn.close()
            return projects
        except Exception as e:
            self.log(f"Error getting projects: {e}", "ERROR")
            return []
    
    def cleanup_dead_workers(self):
        with self.workers_lock:
            dead = [pid for pid, w in self.workers.items() if not w.is_alive()]
            for pid in dead:
                del self.workers[pid]

    def auto_close_expired_reviews(self):
        """Auto-close awaiting_input tickets that have passed their 7-day deadline"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tickets
                SET status = 'done',
                    closed_at = NOW(),
                    closed_by = 'Claude',
                    close_reason = 'auto_closed_7days',
                    review_deadline = NULL,
                    updated_at = NOW()
                WHERE status = 'awaiting_input'
                AND review_deadline IS NOT NULL
                AND review_deadline < NOW()
            """)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            if affected > 0:
                self.log(f"Auto-closed {affected} expired awaiting_input ticket(s)")
        except Exception as e:
            self.log(f"Error auto-closing tickets: {e}", "ERROR")

    def recover_orphaned_tickets(self):
        """Reset tickets that were left in_progress from a previous daemon run (e.g., after reboot)"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()

            # Reset in_progress tickets back to open
            cursor.execute("""
                UPDATE tickets
                SET status='open', updated_at=NOW()
                WHERE status='in_progress'
            """)
            reset_tickets = cursor.rowcount

            # Mark orphaned running sessions as stuck
            cursor.execute("""
                UPDATE execution_sessions
                SET status='stuck', ended_at=NOW()
                WHERE status='running'
            """)
            stuck_sessions = cursor.rowcount

            conn.commit()
            cursor.close()
            conn.close()

            if reset_tickets > 0 or stuck_sessions > 0:
                self.log(f"Startup recovery: reset {reset_tickets} orphaned ticket(s), marked {stuck_sessions} session(s) as stuck")
        except Exception as e:
            self.log(f"Error in startup recovery: {e}", "ERROR")

    def run(self):
        self.log(f"Claude Daemon v3 started (user: {os.getenv('USER', 'unknown')})")
        self.log(f"Max parallel projects: {self.max_parallel}")
        
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE daemon_status SET status='running', started_at=NOW() WHERE id=1")
            conn.commit()
            cursor.close()
            conn.close()
        except: pass

        # Recover any orphaned tickets from previous run
        self.recover_orphaned_tickets()

        while self.running:
            try:
                self.cleanup_dead_workers()
                self.auto_close_expired_reviews()
                projects = self.get_projects_with_open_tickets()
                
                with self.workers_lock:
                    active_count = len([w for w in self.workers.values() if w.is_alive()])
                
                for project in projects:
                    if active_count >= self.max_parallel:
                        break
                    
                    with self.workers_lock:
                        if project['id'] not in self.workers or not self.workers[project['id']].is_alive():
                            worker = ProjectWorker(
                                self,
                                project['id'],
                                project['name'],
                                project['work_path'],
                                self.global_context
                            )
                            worker.start()
                            self.workers[project['id']] = worker
                            active_count += 1
                            self.log(f"Started worker for {project['name']} ({project['open_count']} tickets)")
                
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                time.sleep(POLL_INTERVAL)
        
        self.log("Stopping all workers...")
        with self.workers_lock:
            for worker in self.workers.values():
                worker.stop()
        
        for worker in self.workers.values():
            worker.join(timeout=5)
        
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE daemon_status SET status='stopped' WHERE id=1")
            conn.commit()
            cursor.close()
            conn.close()
        except: pass
        
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        self.log("Claude Daemon stopped")


if __name__ == '__main__':
    daemon = ClaudeDaemon()
    signal.signal(signal.SIGTERM, lambda s, f: setattr(daemon, 'running', False))
    signal.signal(signal.SIGINT, lambda s, f: setattr(daemon, 'running', False))
    daemon.run()

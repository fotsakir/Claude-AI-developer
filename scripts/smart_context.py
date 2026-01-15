#!/usr/bin/env python3
"""
Smart Context Manager for Claude Daemon
Handles: Project Maps, Project Knowledge, Conversation Extractions
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# Token thresholds
MAX_TOTAL_TOKENS = 100000       # Max tokens for conversation history
RECENT_TOKENS_BUDGET = 50000    # Budget for recent messages (full verbatim)
EXTRACTION_THRESHOLD = 50000    # When to trigger extraction
MAX_SINGLE_MESSAGE = 10000      # Truncate messages larger than this
PROJECT_MAP_EXPIRY_DAYS = 7     # Refresh project map after this


class SmartContextManager:
    """Manages smart context for Claude conversations"""

    def __init__(self, db_pool, logger=None):
        self.db_pool = db_pool
        self.logger = logger or (lambda msg, level="INFO": print(f"[{level}] {msg}"))

    def get_db(self):
        return self.db_pool.get_connection()

    def log(self, message, level="INFO"):
        if callable(self.logger):
            self.logger(message, level)

    def count_tokens(self, text: str) -> int:
        """Estimate token count (4 chars ≈ 1 token for English/code)"""
        if not text:
            return 0
        return len(text) // 4

    def truncate_message(self, content: str, max_tokens: int = MAX_SINGLE_MESSAGE) -> str:
        """Truncate message if too large, keeping start and end"""
        if not content:
            return content

        tokens = self.count_tokens(content)
        if tokens <= max_tokens:
            return content

        # Keep first 40% and last 40%, insert truncation notice
        char_limit = max_tokens * 4
        first_part = content[:int(char_limit * 0.4)]
        last_part = content[-int(char_limit * 0.4):]

        return f"{first_part}\n\n[... truncated {tokens - max_tokens} tokens ...]\n\n{last_part}"

    # ═══════════════════════════════════════════════════════════════════════════
    # USER PREFERENCES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM user_preferences WHERE user_id = %s
            """, (user_id,))
            prefs = cursor.fetchone()
            cursor.close()
            conn.close()

            if prefs:
                # Parse JSON fields
                for field in ['programming_style', 'comment_style', 'error_handling',
                              'preferred_tools', 'git_style', 'editor_config',
                              'learned_quirks', 'topics_of_interest', 'things_to_avoid']:
                    if prefs.get(field) and isinstance(prefs[field], str):
                        try:
                            prefs[field] = json.loads(prefs[field])
                        except:
                            pass
            return prefs
        except Exception as e:
            self.log(f"Error getting user preferences: {e}", "ERROR")
            return None

    def build_user_context(self, user_id: str) -> str:
        """Build user context string for system prompt"""
        prefs = self.get_user_preferences(user_id)
        if not prefs:
            return ""

        parts = ["\n=== USER PREFERENCES ==="]

        if prefs.get('language'):
            parts.append(f"Language: {prefs['language']}")
        if prefs.get('response_style'):
            parts.append(f"Response style: {prefs['response_style']}")
        if prefs.get('skill_level'):
            parts.append(f"Skill level: {prefs['skill_level']}")
        if prefs.get('programming_style'):
            parts.append(f"Programming style: {', '.join(prefs['programming_style']) if isinstance(prefs['programming_style'], list) else prefs['programming_style']}")
        if prefs.get('custom_instructions'):
            parts.append(f"Instructions: {prefs['custom_instructions']}")
        if prefs.get('learned_quirks'):
            quirks = prefs['learned_quirks']
            if isinstance(quirks, list):
                parts.append(f"Notes: {'; '.join(quirks)}")

        parts.append("========================\n")
        return '\n'.join(parts) if len(parts) > 2 else ""

    # ═══════════════════════════════════════════════════════════════════════════
    # PROJECT MAP
    # ═══════════════════════════════════════════════════════════════════════════

    def get_project_map(self, project_id: int) -> Optional[Dict]:
        """Get cached project map"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM project_maps
                WHERE project_id = %s AND (expires_at IS NULL OR expires_at > NOW())
            """, (project_id,))
            pmap = cursor.fetchone()
            cursor.close()
            conn.close()

            if pmap:
                for field in ['entry_points', 'key_files', 'tech_stack', 'dependencies', 'design_patterns']:
                    if pmap.get(field) and isinstance(pmap[field], str):
                        try:
                            pmap[field] = json.loads(pmap[field])
                        except:
                            pass
            return pmap
        except Exception as e:
            self.log(f"Error getting project map: {e}", "ERROR")
            return None

    def generate_project_map(self, project_id: int, project_path: str, claude_func=None) -> Optional[Dict]:
        """Generate project map by analyzing the project structure"""
        self.log(f"Generating project map for project {project_id}")

        if not project_path or not os.path.exists(project_path):
            self.log(f"Project path does not exist: {project_path}", "WARNING")
            return None

        try:
            # Gather project information
            tree_output = self._get_tree_output(project_path)
            readme_content = self._read_file_if_exists(os.path.join(project_path, 'README.md'))
            requirements = self._read_file_if_exists(os.path.join(project_path, 'requirements.txt'))
            package_json = self._read_file_if_exists(os.path.join(project_path, 'package.json'))

            # Count files and size
            file_count, total_size = self._get_project_stats(project_path)

            # Detect primary language
            primary_language = self._detect_language(project_path)

            # Build simple map without Claude (for now)
            # TODO: Use claude_func to generate intelligent summary
            map_data = {
                'structure_summary': tree_output[:5000] if tree_output else '',
                'entry_points': json.dumps(self._detect_entry_points(project_path)),
                'key_files': json.dumps([]),
                'tech_stack': json.dumps(self._detect_tech_stack(requirements, package_json)),
                'dependencies': json.dumps({'raw': requirements[:2000]}) if requirements else None,
                'architecture_type': None,
                'design_patterns': json.dumps([]),
                'file_count': file_count,
                'total_size_kb': total_size,
                'primary_language': primary_language,
                'expires_at': datetime.now() + timedelta(days=PROJECT_MAP_EXPIRY_DAYS)
            }

            # Save to database
            conn = self.get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO project_maps
                (project_id, structure_summary, entry_points, key_files, tech_stack,
                 dependencies, architecture_type, design_patterns, file_count,
                 total_size_kb, primary_language, generated_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                ON DUPLICATE KEY UPDATE
                structure_summary = VALUES(structure_summary),
                entry_points = VALUES(entry_points),
                key_files = VALUES(key_files),
                tech_stack = VALUES(tech_stack),
                dependencies = VALUES(dependencies),
                file_count = VALUES(file_count),
                total_size_kb = VALUES(total_size_kb),
                primary_language = VALUES(primary_language),
                generated_at = NOW(),
                expires_at = VALUES(expires_at)
            """, (
                project_id, map_data['structure_summary'], map_data['entry_points'],
                map_data['key_files'], map_data['tech_stack'], map_data['dependencies'],
                map_data['architecture_type'], map_data['design_patterns'],
                map_data['file_count'], map_data['total_size_kb'],
                map_data['primary_language'], map_data['expires_at']
            ))

            # Update project timestamp
            cursor.execute("""
                UPDATE projects SET map_generated_at = NOW() WHERE id = %s
            """, (project_id,))

            conn.commit()
            cursor.close()
            conn.close()

            self.log(f"Project map generated: {file_count} files, {total_size}KB")
            return map_data

        except Exception as e:
            self.log(f"Error generating project map: {e}", "ERROR")
            return None

    def get_or_create_project_map(self, project_id: int, project_path: str) -> Optional[Dict]:
        """Get existing map or create new one"""
        pmap = self.get_project_map(project_id)
        if pmap:
            return pmap
        return self.generate_project_map(project_id, project_path)

    def build_project_map_context(self, project_id: int, project_path: str) -> str:
        """Build project map context string for system prompt"""
        pmap = self.get_or_create_project_map(project_id, project_path)
        if not pmap:
            return ""

        parts = ["\n=== PROJECT STRUCTURE ==="]

        if pmap.get('structure_summary'):
            # Limit structure to reasonable size
            structure = pmap['structure_summary']
            if len(structure) > 2000:
                structure = structure[:2000] + "\n... (truncated)"
            parts.append(structure)

        if pmap.get('tech_stack'):
            tech = pmap['tech_stack']
            if isinstance(tech, list):
                parts.append(f"\nTech Stack: {', '.join(tech)}")

        if pmap.get('entry_points'):
            entries = pmap['entry_points']
            if isinstance(entries, list) and entries:
                entry_str = ', '.join([e.get('file', str(e)) if isinstance(e, dict) else str(e) for e in entries[:5]])
                parts.append(f"Entry Points: {entry_str}")

        if pmap.get('primary_language'):
            parts.append(f"Primary Language: {pmap['primary_language']}")

        parts.append("=========================\n")
        return '\n'.join(parts)

    def _get_tree_output(self, path: str, max_depth: int = 3) -> str:
        """Get directory tree output"""
        try:
            result = subprocess.run(
                ['tree', '-L', str(max_depth), '-I', '__pycache__|node_modules|.git|*.pyc', path],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout if result.returncode == 0 else ""
        except:
            return ""

    def _read_file_if_exists(self, path: str, max_size: int = 10000) -> Optional[str]:
        """Read file content if it exists"""
        try:
            if os.path.exists(path) and os.path.isfile(path):
                with open(path, 'r', errors='ignore') as f:
                    return f.read(max_size)
        except:
            pass
        return None

    def _get_project_stats(self, path: str) -> tuple:
        """Get file count and total size"""
        file_count = 0
        total_size = 0
        try:
            for root, dirs, files in os.walk(path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'venv', '.venv']]
                for f in files:
                    file_count += 1
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
        except:
            pass
        return file_count, total_size // 1024

    def _detect_language(self, path: str) -> str:
        """Detect primary programming language"""
        extensions = {}
        try:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'venv']]
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.java', '.go', '.rs', '.rb']:
                        extensions[ext] = extensions.get(ext, 0) + 1
        except:
            pass

        if not extensions:
            return 'unknown'

        lang_map = {'.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                    '.jsx': 'React', '.tsx': 'React/TypeScript', '.php': 'PHP',
                    '.java': 'Java', '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby'}

        top_ext = max(extensions, key=extensions.get)
        return lang_map.get(top_ext, top_ext)

    def _detect_entry_points(self, path: str) -> List[Dict]:
        """Detect common entry points"""
        entry_files = ['app.py', 'main.py', 'index.js', 'index.ts', 'server.py',
                       'manage.py', 'wsgi.py', 'asgi.py', 'index.php', 'main.go']
        found = []
        try:
            for f in entry_files:
                fp = os.path.join(path, f)
                if os.path.exists(fp):
                    found.append({'file': f, 'purpose': 'Entry point'})
        except:
            pass
        return found

    def _detect_tech_stack(self, requirements: str, package_json: str) -> List[str]:
        """Detect tech stack from dependency files"""
        stack = []

        if requirements:
            if 'flask' in requirements.lower():
                stack.append('Flask')
            if 'django' in requirements.lower():
                stack.append('Django')
            if 'fastapi' in requirements.lower():
                stack.append('FastAPI')
            if 'sqlalchemy' in requirements.lower():
                stack.append('SQLAlchemy')
            if 'pytest' in requirements.lower():
                stack.append('pytest')

        if package_json:
            try:
                pkg = json.loads(package_json)
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                if 'react' in deps:
                    stack.append('React')
                if 'vue' in deps:
                    stack.append('Vue')
                if 'express' in deps:
                    stack.append('Express')
                if 'next' in deps:
                    stack.append('Next.js')
            except:
                pass

        return stack

    # ═══════════════════════════════════════════════════════════════════════════
    # PROJECT KNOWLEDGE
    # ═══════════════════════════════════════════════════════════════════════════

    def get_project_knowledge(self, project_id: int) -> Optional[Dict]:
        """Get learned project knowledge"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM project_knowledge WHERE project_id = %s
            """, (project_id,))
            knowledge = cursor.fetchone()
            cursor.close()
            conn.close()

            if knowledge:
                json_fields = ['coding_patterns', 'naming_conventions', 'file_organization',
                              'known_gotchas', 'error_solutions', 'performance_notes',
                              'architecture_decisions', 'api_conventions', 'testing_patterns',
                              'ci_cd_notes', 'environment_notes', 'security_considerations',
                              'sensitive_files', 'learned_from_tickets']
                for field in json_fields:
                    if knowledge.get(field) and isinstance(knowledge[field], str):
                        try:
                            knowledge[field] = json.loads(knowledge[field])
                        except:
                            pass
            return knowledge
        except Exception as e:
            self.log(f"Error getting project knowledge: {e}", "ERROR")
            return None

    def build_project_knowledge_context(self, project_id: int) -> str:
        """Build project knowledge context string for system prompt"""
        knowledge = self.get_project_knowledge(project_id)
        if not knowledge:
            return ""

        parts = ["\n=== PROJECT KNOWLEDGE ==="]

        if knowledge.get('coding_patterns'):
            patterns = knowledge['coding_patterns']
            if isinstance(patterns, list) and patterns:
                parts.append(f"Coding Patterns: {'; '.join(patterns[:5])}")

        if knowledge.get('known_gotchas'):
            gotchas = knowledge['known_gotchas']
            if isinstance(gotchas, list) and gotchas:
                parts.append(f"Known Gotchas: {'; '.join(gotchas[:5])}")

        if knowledge.get('error_solutions'):
            solutions = knowledge['error_solutions']
            if isinstance(solutions, list) and solutions:
                for sol in solutions[:3]:
                    if isinstance(sol, dict):
                        parts.append(f"- {sol.get('error', '?')}: {sol.get('solution', '?')}")

        if knowledge.get('architecture_decisions'):
            decisions = knowledge['architecture_decisions']
            if isinstance(decisions, list) and decisions:
                for dec in decisions[:3]:
                    if isinstance(dec, dict):
                        parts.append(f"- Decision: {dec.get('decision', '?')} (Reason: {dec.get('reason', '?')})")

        parts.append("=========================\n")
        return '\n'.join(parts) if len(parts) > 2 else ""

    def add_project_knowledge(self, project_id: int, knowledge_type: str, value: Any):
        """Add learned knowledge to project"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)

            # Get existing knowledge
            cursor.execute("SELECT * FROM project_knowledge WHERE project_id = %s", (project_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing
                current = existing.get(knowledge_type)
                if current:
                    try:
                        current_list = json.loads(current) if isinstance(current, str) else current
                    except:
                        current_list = []
                else:
                    current_list = []

                if isinstance(current_list, list):
                    if value not in current_list:
                        current_list.append(value)
                        cursor.execute(f"""
                            UPDATE project_knowledge SET {knowledge_type} = %s, last_updated = NOW()
                            WHERE project_id = %s
                        """, (json.dumps(current_list), project_id))
            else:
                # Create new
                cursor.execute("""
                    INSERT INTO project_knowledge (project_id, {}) VALUES (%s, %s)
                """.format(knowledge_type), (project_id, json.dumps([value])))

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.log(f"Error adding project knowledge: {e}", "ERROR")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONVERSATION EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════════

    def get_extraction(self, ticket_id: int) -> Optional[Dict]:
        """Get latest conversation extraction for ticket"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM conversation_extractions
                WHERE ticket_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (ticket_id,))
            extraction = cursor.fetchone()
            cursor.close()
            conn.close()

            if extraction:
                json_fields = ['decisions', 'problems_solved', 'files_modified',
                              'blocking_issues', 'waiting_for_user', 'external_dependencies',
                              'key_code_snippets', 'important_variables', 'tests_status',
                              'error_patterns', 'important_notes']
                for field in json_fields:
                    if extraction.get(field) and isinstance(extraction[field], str):
                        try:
                            extraction[field] = json.loads(extraction[field])
                        except:
                            pass
            return extraction
        except Exception as e:
            self.log(f"Error getting extraction: {e}", "ERROR")
            return None

    def build_extraction_context(self, ticket_id: int) -> str:
        """Build extraction context string for system prompt"""
        extraction = self.get_extraction(ticket_id)
        if not extraction:
            return ""

        parts = ["\n=== PREVIOUS WORK ON THIS TICKET ==="]

        # IMPORTANT NOTES - Always shown first and prominently!
        if extraction.get('important_notes'):
            notes = extraction['important_notes']
            if isinstance(notes, list) and notes:
                parts.append("\n⚠️ IMPORTANT - ALWAYS REMEMBER:")
                for note in notes[:10]:
                    parts.append(f"  • {note}")
                parts.append("")  # Empty line for visual separation

        if extraction.get('decisions'):
            parts.append("\nDecisions made:")
            for dec in extraction['decisions'][:5]:
                if isinstance(dec, dict):
                    parts.append(f"  - {dec.get('decision', '?')}: {dec.get('reason', '?')}")
                else:
                    parts.append(f"  - {dec}")

        if extraction.get('problems_solved'):
            parts.append("\nProblems solved:")
            for prob in extraction['problems_solved'][:5]:
                if isinstance(prob, dict):
                    parts.append(f"  - {prob.get('problem', '?')}: {prob.get('solution', '?')}")
                else:
                    parts.append(f"  - {prob}")

        if extraction.get('files_modified'):
            files = extraction['files_modified']
            if isinstance(files, list):
                parts.append(f"\nFiles modified: {', '.join(files[:10])}")

        if extraction.get('current_status'):
            parts.append(f"\nCurrent status: {extraction['current_status']}")

        if extraction.get('blocking_issues'):
            issues = extraction['blocking_issues']
            if isinstance(issues, list) and issues:
                parts.append(f"\nBlocking: {', '.join(issues)}")

        if extraction.get('error_patterns'):
            parts.append("\nKnown error patterns:")
            for err in extraction['error_patterns'][:3]:
                if isinstance(err, dict):
                    parts.append(f"  - {err.get('error', '?')}: {err.get('solution', '?')}")

        parts.append("=====================================\n")
        return '\n'.join(parts)

    def _extract_with_haiku(self, conversation_text: List[str], files: List[str]) -> Optional[Dict]:
        """Use Claude Haiku to create intelligent extraction"""
        try:
            # Build prompt for Haiku
            prompt = f"""Analyze this conversation and extract key information in JSON format.

CONVERSATION:
{chr(10).join(conversation_text[-30:])}

FILES MENTIONED: {', '.join(files[:20]) if files else 'None'}

Respond with ONLY a JSON object (no markdown, no explanation):
{{
    "decisions": ["decision 1", "decision 2", ...],
    "problems_solved": ["problem 1: solution", "problem 2: solution", ...],
    "current_status": "Brief status of where things stand",
    "key_info": "Most important technical details to remember (configs, values, patterns used)",
    "important_notes": ["note 1", "note 2", ...]
}}

IMPORTANT_NOTES EXTRACTION:
Extract any user instructions, warnings, rules, or things to always remember.
Understand the SEMANTIC MEANING, not just keywords. Look for:
- Explicit rules ("never do X", "always do Y")
- Warnings about gotchas, pitfalls, or things to avoid
- User preferences expressed strongly or repeatedly
- Constraints or limitations the user mentioned
- Things the user emphasized (via caps, repetition, or strong language)
- Any instruction about HOW the AI should behave or work

These notes will be shown to the AI in EVERY future conversation about this ticket.

Keep each item concise (under 100 chars). Focus on technical decisions and implementations."""

            # Call Claude Haiku using CLI
            result = subprocess.run(
                ['/home/claude/.local/bin/claude', '--model', 'haiku', '--print'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
                cwd='/tmp'
            )

            if result.returncode == 0 and result.stdout:
                # Parse JSON response
                response = result.stdout.strip()
                # Remove markdown code blocks if present
                if response.startswith('```'):
                    response = response.split('```')[1]
                    if response.startswith('json'):
                        response = response[4:]
                    response = response.strip()

                extraction = json.loads(response)
                self.log(f"Haiku extraction successful: {len(extraction.get('decisions', []))} decisions")
                return extraction
            else:
                self.log(f"Haiku extraction failed: {result.stderr[:200] if result.stderr else 'no output'}", "WARNING")
                return None

        except subprocess.TimeoutExpired:
            self.log("Haiku extraction timed out", "WARNING")
            return None
        except json.JSONDecodeError as e:
            self.log(f"Haiku response not valid JSON: {e}", "WARNING")
            return None
        except Exception as e:
            self.log(f"Haiku extraction error: {e}", "WARNING")
            return None

    def create_extraction(self, ticket_id: int, messages: List[Dict], claude_func=None) -> Optional[Dict]:
        """Create extraction from older messages using Claude Haiku"""

        self.log(f"Creating extraction for ticket {ticket_id} from {len(messages)} messages")

        try:
            # Build conversation text for summarization
            conversation_text = []
            files = set()
            import re

            for msg in messages:
                content = msg.get('content', '') or ''
                role = msg.get('role', 'unknown')

                if content and role in ['user', 'assistant']:
                    conversation_text.append(f"[{role.upper()}]: {content[:2000]}")

                    # Extract file references
                    file_matches = re.findall(r'[\w./]+\.(py|js|ts|jsx|tsx|php|html|css|sql|json|yaml|yml|md)', content)
                    files.update(file_matches)

            # Calculate tokens before
            tokens_before = sum(self.count_tokens(m.get('content', '')) for m in messages)

            # Try to get intelligent extraction using Claude Haiku
            extraction_result = self._extract_with_haiku(conversation_text, list(files))

            if extraction_result:
                decisions = extraction_result.get('decisions', [])
                problems = extraction_result.get('problems_solved', [])
                current_status = extraction_result.get('current_status', '')
                key_info = extraction_result.get('key_info', '')
                important_notes = extraction_result.get('important_notes', [])
            else:
                # Fallback to basic extraction
                decisions = []
                problems = []
                current_status = f"Processed {len(messages)} messages"
                key_info = ""
                important_notes = []

            extraction_data = {
                'decisions': json.dumps(decisions[:10]),
                'problems_solved': json.dumps(problems[:10]),
                'files_modified': json.dumps(list(files)[:20]),
                'current_status': current_status or f"Processed {len(messages)} messages",
                'blocking_issues': json.dumps([]),
                'waiting_for_user': json.dumps([]),
                'key_code_snippets': json.dumps([key_info] if key_info else []),
                'tests_status': json.dumps({}),
                'error_patterns': json.dumps([]),
                'important_notes': json.dumps(important_notes[:15]),
                'covers_msg_from_id': messages[0].get('id') if messages else None,
                'covers_msg_to_id': messages[-1].get('id') if messages else None,
                'messages_summarized': len(messages),
                'tokens_before': tokens_before,
                'tokens_after': self.count_tokens(json.dumps(decisions) + json.dumps(problems) + current_status)
            }

            # Save to database
            conn = self.get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO conversation_extractions
                (ticket_id, decisions, problems_solved, files_modified, current_status,
                 blocking_issues, waiting_for_user, key_code_snippets, tests_status, error_patterns,
                 important_notes, covers_msg_from_id, covers_msg_to_id, messages_summarized, tokens_before, tokens_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_id, extraction_data['decisions'], extraction_data['problems_solved'],
                extraction_data['files_modified'], extraction_data['current_status'],
                extraction_data['blocking_issues'], extraction_data['waiting_for_user'],
                extraction_data['key_code_snippets'], extraction_data['tests_status'],
                extraction_data['error_patterns'], extraction_data['important_notes'],
                extraction_data['covers_msg_from_id'], extraction_data['covers_msg_to_id'],
                extraction_data['messages_summarized'], extraction_data['tokens_before'],
                extraction_data['tokens_after']
            ))

            # Mark messages as summarized
            if messages:
                msg_ids = [m.get('id') for m in messages if m.get('id')]
                if msg_ids:
                    placeholders = ','.join(['%s'] * len(msg_ids))
                    cursor.execute(f"""
                        UPDATE conversation_messages SET is_summarized = TRUE
                        WHERE id IN ({placeholders})
                    """, msg_ids)

            conn.commit()
            cursor.close()
            conn.close()

            self.log(f"Extraction created: {tokens_before} tokens -> {extraction_data['tokens_after']} tokens")

            # Update project_knowledge with learnings from this ticket
            try:
                self._update_project_knowledge_from_extraction(
                    ticket_id, decisions, problems, important_notes
                )
            except Exception as e:
                self.log(f"Warning: Could not update project knowledge: {e}", "WARNING")

            return extraction_data

        except Exception as e:
            self.log(f"Error creating extraction: {e}", "ERROR")
            return None

    def _update_project_knowledge_from_extraction(self, ticket_id: int, decisions: List,
                                                   problems: List, important_notes: List):
        """Update project_knowledge table with learnings from extraction"""
        try:
            # Get project_id from ticket
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT project_id FROM tickets WHERE id = %s", (ticket_id,))
            ticket = cursor.fetchone()

            if not ticket:
                cursor.close()
                conn.close()
                return

            project_id = ticket['project_id']

            # Check if project_knowledge exists
            cursor.execute("SELECT id FROM project_knowledge WHERE project_id = %s", (project_id,))
            existing = cursor.fetchone()

            if not existing:
                # Create new project_knowledge record
                cursor.execute("""
                    INSERT INTO project_knowledge (project_id, known_gotchas, error_solutions,
                                                   architecture_decisions, learned_from_tickets)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    project_id,
                    json.dumps(important_notes[:10]) if important_notes else '[]',
                    json.dumps(problems[:10]) if problems else '[]',
                    json.dumps(decisions[:10]) if decisions else '[]',
                    json.dumps([ticket_id])
                ))
                self.log(f"Created project_knowledge for project {project_id}")
            else:
                # Update existing - merge with existing data
                cursor.execute("""
                    SELECT known_gotchas, error_solutions, architecture_decisions, learned_from_tickets
                    FROM project_knowledge WHERE project_id = %s
                """, (project_id,))
                existing_data = cursor.fetchone()

                # Parse existing JSON
                def parse_json_field(field):
                    if not field:
                        return []
                    if isinstance(field, str):
                        try:
                            return json.loads(field)
                        except:
                            return []
                    return field if isinstance(field, list) else []

                existing_gotchas = parse_json_field(existing_data.get('known_gotchas'))
                existing_errors = parse_json_field(existing_data.get('error_solutions'))
                existing_decisions = parse_json_field(existing_data.get('architecture_decisions'))
                existing_tickets = parse_json_field(existing_data.get('learned_from_tickets'))

                # Merge new data (avoid duplicates)
                for note in (important_notes or [])[:10]:
                    if note and note not in existing_gotchas:
                        existing_gotchas.append(note)

                for prob in (problems or [])[:10]:
                    if prob and prob not in existing_errors:
                        existing_errors.append(prob)

                for dec in (decisions or [])[:10]:
                    if dec and dec not in existing_decisions:
                        existing_decisions.append(dec)

                if ticket_id not in existing_tickets:
                    existing_tickets.append(ticket_id)

                # Keep last 20 items max
                cursor.execute("""
                    UPDATE project_knowledge SET
                        known_gotchas = %s,
                        error_solutions = %s,
                        architecture_decisions = %s,
                        learned_from_tickets = %s,
                        last_updated = NOW()
                    WHERE project_id = %s
                """, (
                    json.dumps(existing_gotchas[-20:]),
                    json.dumps(existing_errors[-20:]),
                    json.dumps(existing_decisions[-20:]),
                    json.dumps(existing_tickets[-50:]),
                    project_id
                ))
                self.log(f"Updated project_knowledge for project {project_id} from ticket {ticket_id}")

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            self.log(f"Error updating project knowledge: {e}", "ERROR")

    # ═══════════════════════════════════════════════════════════════════════════
    # SMART HISTORY
    # ═══════════════════════════════════════════════════════════════════════════

    def get_smart_history(self, ticket_id: int) -> List[Dict]:
        """Get conversation history - ONLY unsummarized messages"""
        try:
            conn = self.get_db()
            cursor = conn.cursor(dictionary=True)

            # Get ONLY unsummarized messages
            cursor.execute("""
                SELECT id, role, content, tool_name, tool_input, token_count, is_summarized
                FROM conversation_messages
                WHERE ticket_id = %s AND is_summarized = FALSE
                ORDER BY created_at ASC
            """, (ticket_id,))
            unsummarized_messages = cursor.fetchall()
            cursor.close()
            conn.close()

            if not unsummarized_messages:
                return []

            # Calculate/update token counts if needed
            for msg in unsummarized_messages:
                if not msg.get('token_count') or msg['token_count'] == 0:
                    msg['token_count'] = self.count_tokens(msg.get('content', ''))

            # Calculate total tokens of unsummarized
            total_tokens = sum(m.get('token_count', 0) for m in unsummarized_messages)

            # If under threshold, return all unsummarized
            if total_tokens < EXTRACTION_THRESHOLD:
                return unsummarized_messages

            # Over threshold - need to extract older messages
            # Select recent messages within budget
            recent = []
            recent_tokens = 0

            for msg in reversed(unsummarized_messages):
                msg_tokens = msg.get('token_count', 0)

                # Truncate very large messages
                if msg_tokens > MAX_SINGLE_MESSAGE:
                    msg['content'] = self.truncate_message(msg.get('content', ''), MAX_SINGLE_MESSAGE)
                    msg_tokens = MAX_SINGLE_MESSAGE

                if recent_tokens + msg_tokens > RECENT_TOKENS_BUDGET:
                    break

                recent.insert(0, msg)
                recent_tokens += msg_tokens

            # Extract older unsummarized messages
            if len(recent) < len(unsummarized_messages):
                older_messages = unsummarized_messages[:-len(recent)] if recent else unsummarized_messages
                if older_messages:
                    self.create_extraction(ticket_id, older_messages)

            return recent

        except Exception as e:
            self.log(f"Error getting smart history: {e}", "ERROR")
            return []

    def update_message_token_count(self, message_id: int, token_count: int):
        """Update token count for a message"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversation_messages SET token_count = %s WHERE id = %s
            """, (token_count, message_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.log(f"Error updating token count: {e}", "ERROR")

    # ═══════════════════════════════════════════════════════════════════════════
    # BUILD COMPLETE CONTEXT
    # ═══════════════════════════════════════════════════════════════════════════

    def build_android_context(self, ticket: Dict) -> str:
        """Build Android development context when project is mobile type"""
        project_type = ticket.get('project_type', '')
        android_device_type = ticket.get('android_device_type', 'none')

        mobile_types = ['capacitor', 'react_native', 'flutter', 'native_android']
        if project_type not in mobile_types or android_device_type == 'none':
            return ""

        parts = ["\n=== ANDROID DEVELOPMENT ==="]
        parts.append(f"Project Type: {project_type}")

        if android_device_type == 'server':
            parts.append("""
Android Emulator: Server-based (Redroid)
- ADB device: localhost:5556
- Use 'adb connect localhost:5556' if disconnected
- Install APK: adb -s localhost:5556 install app.apk
- View logs: adb -s localhost:5556 logcat
- Screen capture: adb -s localhost:5556 exec-out screencap -p > screen.png
- The emulator runs in Docker, accessible via web interface""")
        elif android_device_type == 'remote':
            remote_host = ticket.get('android_remote_host', '')
            remote_port = ticket.get('android_remote_port', 5555)
            parts.append(f"""
Android Device: Remote ADB
- ADB device: {remote_host}:{remote_port}
- Connect: adb connect {remote_host}:{remote_port}
- Install APK: adb -s {remote_host}:{remote_port} install app.apk
- View logs: adb -s {remote_host}:{remote_port} logcat""")

        # Framework-specific guidance
        if project_type == 'capacitor':
            parts.append("""
Capacitor.js Commands:
- Build: npx cap build android
- Sync: npx cap sync android
- Open Android Studio: npx cap open android
- Run on device: npx cap run android""")
        elif project_type == 'react_native':
            parts.append("""
React Native Commands:
- Start Metro: npx react-native start
- Run Android: npx react-native run-android
- Build APK: cd android && ./gradlew assembleRelease
- Logs: npx react-native log-android""")
        elif project_type == 'flutter':
            parts.append("""
Flutter Commands:
- Run: flutter run
- Build APK: flutter build apk
- Build App Bundle: flutter build appbundle
- Logs: flutter logs""")
        elif project_type == 'native_android':
            parts.append("""
Android Native Commands:
- Build: ./gradlew build
- Install: ./gradlew installDebug
- Run tests: ./gradlew test
- Clean: ./gradlew clean""")

        parts.append("============================\n")
        return '\n'.join(parts)

    def build_dotnet_context(self, ticket: Dict) -> str:
        """Build .NET development context when project is dotnet type"""
        project_type = ticket.get('project_type', '')

        if project_type != 'dotnet':
            return ""

        dotnet_port = ticket.get('dotnet_port', 5001)
        app_path = ticket.get('app_path', '')
        project_code = ticket.get('code', '').lower()

        parts = ["\n=== .NET DEVELOPMENT ==="]
        parts.append(f"Project Type: ASP.NET Core / .NET 8")
        parts.append(f"App Directory: {app_path}")
        parts.append(f"Internal Port: {dotnet_port}")
        parts.append(f"""
.NET Commands:
- Create console app: dotnet new console
- Create web API: dotnet new webapi
- Create MVC app: dotnet new mvc
- Create Blazor app: dotnet new blazor
- Build: dotnet build
- Run: dotnet run
- Run with port: dotnet run --urls=http://127.0.0.1:{dotnet_port}
- Test: dotnet test
- Publish: dotnet publish -c Release

After building, the app will be accessible at:
  https://SERVER_IP:9867/{project_code}/

Service Management:
- Start: sudo systemctl start codehero-dotnet-{project_code}
- Stop: sudo systemctl stop codehero-dotnet-{project_code}
- Status: sudo systemctl status codehero-dotnet-{project_code}
- Logs: journalctl -u codehero-dotnet-{project_code} -f

Important: After publishing, restart the service to apply changes.
""")
        parts.append("============================\n")
        return '\n'.join(parts)

    def build_full_context(self, ticket: Dict, user_id: str = None) -> Dict:
        """Build complete context for Claude API call"""
        project_id = ticket.get('project_id')
        ticket_id = ticket.get('id')
        project_path = ticket.get('web_path') or ticket.get('app_path')

        context_parts = []

        # 1. User preferences
        if user_id:
            user_context = self.build_user_context(user_id)
            if user_context:
                context_parts.append(user_context)

        # 2. Project map
        if project_id and project_path:
            map_context = self.build_project_map_context(project_id, project_path)
            if map_context:
                context_parts.append(map_context)

        # 3. Project knowledge
        if project_id:
            knowledge_context = self.build_project_knowledge_context(project_id)
            if knowledge_context:
                context_parts.append(knowledge_context)

        # 4. Android development context (for mobile projects)
        android_context = self.build_android_context(ticket)
        if android_context:
            context_parts.append(android_context)

        # 5. .NET development context (for dotnet projects)
        dotnet_context = self.build_dotnet_context(ticket)
        if dotnet_context:
            context_parts.append(dotnet_context)

        # 7. Ticket extraction (if exists)
        if ticket_id:
            extraction_context = self.build_extraction_context(ticket_id)
            if extraction_context:
                context_parts.append(extraction_context)

        # 8. Recent messages
        history = self.get_smart_history(ticket_id) if ticket_id else []

        return {
            'system_context': '\n'.join(context_parts),
            'history': history,
            'has_extraction': bool(self.get_extraction(ticket_id)) if ticket_id else False
        }

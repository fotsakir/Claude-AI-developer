#!/usr/bin/env python3
"""
HeroAgent - Coding Agent for CodeHero

A lightweight Python coding agent that serves as a drop-in replacement for Claude Code.
Supports multiple AI providers and is 100% compatible with the CodeHero daemon.

Usage:
    heroagent -p "Create a login page"
    heroagent --model opus -p "Fix the bug"
    heroagent --provider gemini --model gemini-2.0-flash -p "task"
    heroagent --dangerously-skip-permissions -p "task"
"""

import argparse
import json
import os
import sys
import traceback
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, Config
from output.stream import StreamOutput
from hooks.manager import HookManager, Permission, PermissionDeniedError
from tools import BashTool, ReadTool, WriteTool, EditTool, GlobTool, GrepTool, WebFetchTool, ScreenshotTool
from tools.base import BaseTool, ToolResult


__version__ = '1.0.0'


# System prompt for the agent - includes full global context rules
SYSTEM_PROMPT = """You are HeroAgent, a coding assistant that EXECUTES tasks using tools.

> **MISSION:** Build simple, testable code that AI can maintain without human help.

=== EXECUTION RULES ===
1. DO NOT describe what you will do - ACTUALLY DO IT by calling tools
2. DO NOT think out loud - just execute tools and report results
3. Execute tools IMMEDIATELY when needed
4. If a tool fails, try an alternative approach
5. Be concise. No lengthy explanations.

=== AVAILABLE TOOLS ===
- Bash: Execute shell commands (timeout: 120s)
- Read: Read files AND images (you have vision!)
- Write: Create or overwrite files
- Edit: Edit files with search/replace
- Glob: Find files by pattern
- Grep: Search file contents
- WebFetch: Fetch and analyze web pages
- Screenshot: FULL PAGE VERIFICATION - takes screenshots AND captures:
  • Console errors (JS errors - must be ZERO!)
  • Failed requests (404, CORS - must be ZERO!)
  • All links for verification

=== PART 1: CRITICAL RULES ===

PROTECTED PATHS - FORBIDDEN:
/opt/codehero/, /etc/codehero/, /var/backups/codehero/
/etc/nginx/, /etc/systemd/, /home/claude/.claude*

YOUR WORKSPACE ONLY:
- Web projects: /var/www/projects/{project}/
- App projects: /opt/apps/{project}/
- Reference projects: /opt/codehero/references/{project}/ (READ-ONLY!)

SECURITY - NON-NEGOTIABLE:
- SQL: ALWAYS prepared statements, NEVER f"SELECT * FROM users WHERE id = {id}"
- Output: ALWAYS escape - htmlspecialchars($input, ENT_QUOTES, 'UTF-8')
- Passwords: ALWAYS bcrypt.hash(password), NEVER store plain
- Credentials: NEVER hardcode, ALWAYS use .env files

=== PART 2: CODE QUALITY & READABILITY ===

**CRITICAL: Write HUMAN-READABLE code. NO obfuscation!**

PHILOSOPHY: DIRECT EDITING ON PRODUCTION
Code must be editable directly on the production server:
1. Find the file → 2. Open it → 3. Fix the line → 4. Done!

This means:
✅ Source code format - NOT minified, NOT bundled
✅ One file = one purpose - NOT thousands of lines in one file
✅ Readable names - Know what it does by reading it
✅ No build required for hotfixes

NEVER use (unless user explicitly requests):
❌ Webpack/Vite bundles in production
❌ TypeScript (requires compilation)
❌ Minification (can't read/debug)
❌ One giant file with everything

**Performance is NOT a priority.** Prefer:
- Readable code over fast code
- Multiple small files over one bundled file
- Easy debugging over micro-optimizations

TEAM MINDSET:
- Write as if a junior developer reads it at 3am
- If you leave, can someone else continue?
- Comment the WHY, not the WHAT

CODE MUST BE:
✅ Well-formatted and properly indented
✅ With meaningful comments explaining complex logic
✅ Using descriptive, human-readable names
✅ Easy to understand and maintain
✅ Properly structured with clear separation of concerns

NAMING - ALWAYS HUMAN-READABLE:
| Type | Convention | Good Example | BAD Example |
| Variables | descriptive | userEmail, totalPrice | x, tmp, data1 |
| Functions | verb + noun | calculateTotal() | calc(), doIt() |
| Classes | noun, clear purpose | UserService | US, Handler1 |
| Files | describe content | user_authentication.py | ua.py, file1.py |
| Folders | logical grouping | components/, services/ | c/, s/, misc/ |
| Constants | UPPER_SNAKE | MAX_LOGIN_ATTEMPTS | MLA, X |

NAMING CONVENTIONS BY LANGUAGE:
| Type | Convention | Example |
| Python files | snake_case | user_service.py |
| PHP files | PascalCase | UserService.php |
| Classes | PascalCase | UserService |
| Functions | camelCase | createUser() |
| Constants | UPPER_SNAKE | MAX_RETRIES |
| DB tables | snake_case plural | order_items |

COMMENTS - Required for:
- Complex algorithms or business logic
- Non-obvious code decisions
- API endpoints and their parameters
- Configuration values and their purpose
- TODO items with context

NEVER:
❌ Single-letter variable names (except loop counters i, j, k)
❌ Abbreviated names that aren't universally known
❌ Minified or obfuscated code in source files
❌ Magic numbers without explanation
❌ Copy-pasted code without understanding

LANGUAGE DEFAULTS:
- **JavaScript by default** - Use .js files, NOT TypeScript (.ts)
- Only use TypeScript if: project already has tsconfig.json OR user explicitly requests it
- If user requests Vue/React: Use .js/.jsx, NOT .ts/.tsx

=== PART 3: WRITING CODE ===

ERROR HANDLING - Never silent failures:
try:
    do_something()
except SpecificError as e:
    logger.error(f"Failed to do X: {e}")
    raise

NULL CHECKS - Always check first:
if not user:
    return "Hello Guest"
return f"Hello {user.name}"

TIMEOUTS - Never wait forever:
response = requests.get(url, timeout=10)
| HTTP API | 10-30s | DB query | 5-30s | File upload | 60-120s |

TRANSACTIONS - All or nothing:
try:
    db.begin()
    order = create_order(user, amount)
    charge_card(user, amount)
    db.commit()
except:
    db.rollback()
    raise

IDEMPOTENCY - Safe to run twice:
existing = db.query("SELECT id FROM users WHERE email = ?", [email])
if existing:
    return existing['id']
db.execute("INSERT INTO users (email) VALUES (?)", [email])

INPUT VALIDATION:
- Email: check not empty, max 254 chars, valid format
- Files: check extension in whitelist, max size (10MB)

=== PART 4: DEFAULT TECH STACK ===

**USER PREFERENCE ALWAYS WINS!** If user specifies a technology, use that.
**NO BUILD STEP!** All code must be directly editable on production server.

| Project Type | Default Stack |
|--------------|---------------|
| Dashboard / Admin / ERP | PHP + Alpine.js + Tailwind CSS |
| Landing Page / Marketing | HTML + Alpine.js + Tailwind CSS |
| Simple Website | HTML + Tailwind CSS |
| API / Backend | Based on project's tech_stack |

WHY NOT Vue/React with build tools:
❌ Vue + Vite = requires npm run build, can't hotfix on server
❌ React + Webpack = bundled output, needs source maps
❌ TypeScript = requires compilation

LIBRARIES - Download locally (NO CDN in production):
```bash
# Download once at project setup
mkdir -p assets/lib
curl -o assets/lib/alpine.min.js https://unpkg.com/alpinejs@3/dist/cdn.min.js
curl -o assets/lib/tailwind.js https://cdn.tailwindcss.com/3.4.1
curl -o assets/lib/chart.min.js https://cdn.jsdelivr.net/npm/chart.js/dist/chart.umd.min.js
```

For Dashboards (PHP + Alpine.js):
```html
<script src="assets/lib/tailwind.js"></script>
<script defer src="assets/lib/alpine.min.js"></script>
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <nav x-show="open">...</nav>
</div>
```

Why this works:
✅ Edit PHP/HTML directly on server
✅ No build step, no npm, no node_modules
✅ Works offline (no CDN dependency)
✅ Hotfix at 3am = edit file, done

For Complex Tables (server-side with Alpine):
```php
<table x-data="{ selected: [] }">
    <?php foreach($rows as $row): ?>
    <tr @click="selected.push(<?= $row['id'] ?>)">...</tr>
    <?php endforeach; ?>
</table>
```

If user EXPLICITLY requests Vue/React: OK, but warn about build step requirement.

DOWNLOAD ALL ASSETS LOCALLY:
- JS libraries → assets/lib/
- CSS frameworks → assets/lib/
- Fonts → assets/fonts/
- Images/Photos → assets/images/ (NO placeholder.com!)
- For avatars: use ui-avatars.com OR download

Exceptions (MUST be CDN): Google Maps API, Stripe.js, PayPal SDK, reCAPTCHA

=== PART 5: UI RULES ===

PLAYWRIGHT URL & SCREENSHOTS:
URL format: https://127.0.0.1:9867/{folder_name}/
Always use: ignore_https_errors=True, full_page=True
Take BOTH desktop (1920x1080) and mobile (375x667)

UI VERIFICATION (MANDATORY):
1. Use Screenshot tool (captures screenshots + console errors + failed requests)
2. CHECK: console_errors must be [] (empty!)
3. CHECK: failed_requests must be [] (empty!)
4. Read screenshots with Read tool - ACTUALLY LOOK AT THEM!
5. Check server logs: sudo tail -20 /var/log/nginx/*-error.log
6. Check for visual issues below
7. Fix ALL issues → Screenshot again → Repeat until ZERO errors!

COMMON UI KILLERS (Auto-fix without asking):
| Problem | Bad | Fix To |
| Giant padding/margins | 48px, 64px, 128px | 16px or 24px max |
| Oversized icons | 96px, 128px | 32px-48px |
| Excessive spacing | gap: 48px | gap: 16px |
| Huge text (not H1) | 3rem | 1.1rem-1.5rem |

GOOD SIZING REFERENCE:
| Element | Good Size |
| Header height | 60-80px |
| Card padding | 16-24px |
| Card gap | 16-24px |
| Small icons | 24-32px |
| Medium icons | 40-48px |
| Section padding | 32-48px |
| H1 | 2-3rem | H2 | 1.5-2rem | Body | 1rem (16px) |

VERIFICATION CHECKLIST (ALL MUST PASS!):
□ Console errors = 0? (from Screenshot tool)
□ Failed requests = 0? (from Screenshot tool)
□ Server logs clean? (sudo tail -20 /var/log/nginx/*-error.log)
□ Text contrast OK? (no dark-on-dark, light-on-light)
□ No giant empty white spaces?
□ Icons/images proportional to containers?
□ Spacing consistent (8px, 12px, 16px, 24px multiples)?
□ Text readable (min 14px body, 16px ideal)?
□ Responsive (no horizontal scroll on mobile)?
□ All links working?

LINK & URL HANDLING:
Projects are in subfolders: https://IP:9867/mysite/
ALWAYS use relative paths, NOT absolute with /

From /mysite/index.php:
✅ href="about.php" | href="pages/contact.php"
❌ href="/about.php" (goes to server root!)

From /mysite/pages/about.php:
✅ href="../index.php" | src="../images/logo.png"

=== PART 6: VERIFICATION ===

BEFORE FINISHING CHECKLIST:
□ Runs without errors?
□ Main functionality works?
□ Edge cases (null, empty, large data)?
□ Test script passes?

ASK ONLY WHEN NECESSARY:
Default behavior: PROCEED autonomously. Only ask if truly stuck.

Ask ONLY if:
- Requirements are ambiguous AND cannot make reasonable assumption
- Multiple valid approaches AND choice significantly affects outcome
- Action might cause data loss or break existing functionality

Do NOT ask for:
- Minor implementation details (just pick one)
- Styling preferences (follow existing patterns)
- Confirmation of your plan (just do it)

=== COMPLETION ===

When task is complete, say "TASK COMPLETED" and summarize:
- Files created/modified
- Verification results: console_errors=0, failed_requests=0
- Server logs: clean
- Preview URL

DO NOT:
- Mark complete with console_errors > 0
- Mark complete with failed_requests > 0
- Mark complete without checking server logs
- Mark complete without verifying screenshots
- Use CDN instead of downloading locally
- Use placeholder.com for images
- Modify protected paths
- Hardcode credentials
- Skip error handling
- Use giant spacing in UI

=== SERVER INFO ===
Ubuntu 24.04 | PHP 8.3 | Node.js 22.x | MySQL 8.0 | Python 3.12
Ports: Admin=9453, Projects=9867, MySQL=3306"""


class HeroAgent:
    """Main agent class that orchestrates the coding agent."""

    def __init__(
        self,
        config: Config,
        output: StreamOutput,
        skip_permissions: bool = False,
        cwd: Optional[str] = None,
        verbose: bool = False,
    ):
        """Initialize the agent.

        Args:
            config: Configuration object
            output: Output handler
            skip_permissions: Skip permission prompts (autonomous mode)
            cwd: Working directory
            verbose: Enable verbose logging
        """
        self.config = config
        self.output = output
        self.skip_permissions = skip_permissions
        self.cwd = cwd or os.getcwd()
        self.verbose = verbose

        # Initialize tools
        self.tools: Dict[str, BaseTool] = {}
        self._init_tools()

        # Initialize hook manager
        hook_script = config.get_hook_script()
        self.hook_manager = HookManager(
            hook_script=hook_script,
            skip_permissions=skip_permissions
        )

        # Initialize provider (lazy)
        self.provider = None
        self.provider_name = None
        self.model = None

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _init_tools(self):
        """Initialize built-in tools."""
        tool_config = {
            'cwd': self.cwd,
            **self.config.get_tool_config('bash')
        }
        self.tools['Bash'] = BashTool(tool_config)

        self.tools['Read'] = ReadTool(self.config.get_tool_config('read'))
        self.tools['Write'] = WriteTool(self.config.get_tool_config('write'))
        self.tools['Edit'] = EditTool(self.config.get_tool_config('edit'))
        self.tools['Glob'] = GlobTool(self.config.get_tool_config('glob'))
        self.tools['Grep'] = GrepTool(self.config.get_tool_config('grep'))
        self.tools['WebFetch'] = WebFetchTool(self.config.get_tool_config('webfetch'))
        self.tools['Screenshot'] = ScreenshotTool(self.config.get_tool_config('screenshot'))

    def _init_provider(self, provider_name: str, model: str):
        """Initialize the AI provider.

        Args:
            provider_name: Provider name
            model: Model name or alias
        """
        self.provider_name = provider_name
        self.model = model

        # Resolve model alias
        actual_model = self.config.get_model_name(model, provider_name)

        if provider_name == 'anthropic':
            from providers.anthropic import AnthropicProvider
            api_key = self.config.get_api_key('anthropic')
            self.provider = AnthropicProvider(api_key=api_key, model=actual_model)
        elif provider_name == 'gemini':
            from providers.gemini import GeminiProvider
            api_key = self.config.get_api_key('gemini')
            self.provider = GeminiProvider(api_key=api_key, model=actual_model)
        elif provider_name == 'grok':
            from providers.grok import GrokProvider
            api_key = self.config.get_api_key('grok')
            provider_config = self.config.get_provider_config('grok')
            self.provider = GrokProvider(
                api_key=api_key,
                model=actual_model,
                base_url=provider_config.get('base_url')
            )
        elif provider_name == 'openai':
            from providers.openai import OpenAIProvider
            api_key = self.config.get_api_key('openai')
            self.provider = OpenAIProvider(api_key=api_key, model=actual_model)
        elif provider_name == 'ollama':
            from providers.ollama import OllamaProvider
            provider_config = self.config.get_provider_config('ollama')
            self.provider = OllamaProvider(
                model=actual_model,
                base_url=provider_config.get('base_url', 'http://localhost:11434')
            )
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        self.provider.set_model(actual_model)
        self.provider.set_system_prompt(SYSTEM_PROMPT)

    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """Get tool specifications for the AI provider.

        Returns:
            List of tool specifications
        """
        return [tool.to_tool_spec() for tool in self.tools.values()]

    def execute_tool(self, name: str, tool_input: Dict[str, Any]) -> ToolResult:
        """Execute a tool with permission checking.

        Args:
            name: Tool name
            tool_input: Tool input parameters

        Returns:
            Tool execution result
        """
        # Check permission
        permission = self.hook_manager.check_permission(name, tool_input)

        if permission == Permission.DENY:
            return ToolResult(
                output=f"Permission denied for {name}",
                is_error=True
            )

        if permission == Permission.ASK:
            # In semi-autonomous mode, block and report
            # The daemon can handle user prompts; CLI blocks by default
            self.output.log(f"Permission required for {name} - blocking (use --dangerously-skip-permissions to allow)", level='warning')
            return ToolResult(
                output=f"Permission required for {name}. Operation blocked in semi-autonomous mode.",
                is_error=True
            )

        # Get tool
        tool = self.tools.get(name)
        if not tool:
            return ToolResult(
                output=f"Unknown tool: {name}",
                is_error=True
            )

        # Execute
        try:
            return tool.execute(**tool_input)
        except Exception as e:
            return ToolResult(
                output=f"Tool execution error: {str(e)}",
                is_error=True
            )

    def run(self, prompt: str, provider_name: str, model: str) -> bool:
        """Run the agent with a prompt.

        Args:
            prompt: User prompt/task
            provider_name: AI provider to use
            model: Model name or alias

        Returns:
            True if task completed successfully
        """
        # Initialize provider
        self._init_provider(provider_name, model)

        # Add initial message
        self.messages.append({
            'role': 'user',
            'content': prompt
        })

        # Get tool specs
        tools = self.get_tool_specs()

        # Agent loop
        max_iterations = 50
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                # Get response from provider
                if self.verbose:
                    self.output.log(f"Iteration {iteration}: Calling provider")

                response = self.provider.chat(
                    messages=self.messages,
                    tools=tools,
                    max_tokens=self.config.max_tokens
                )

                # Track usage
                self.total_input_tokens += response.usage.get('input_tokens', 0)
                self.total_output_tokens += response.usage.get('output_tokens', 0)

                # Update output handler with current usage
                self.output.set_usage({
                    'input_tokens': self.total_input_tokens,
                    'output_tokens': self.total_output_tokens
                })

                # Build tool_uses list for combined output
                tool_uses = None
                if response.tool_calls:
                    tool_uses = [{
                        'id': tc.id,
                        'name': tc.name,
                        'input': tc.input
                    } for tc in response.tool_calls]

                # Emit combined assistant message (text + tool_uses)
                # This matches Claude Code's format for daemon compatibility
                if response.content or tool_uses:
                    self.output.assistant(response.content or '', tool_uses)

                # Handle text-only response
                if response.content and not response.tool_calls:
                    self.messages.append({
                        'role': 'assistant',
                        'content': response.content
                    })

                    # Check for completion
                    if self.config.completion_marker in response.content:
                        self._emit_result(True)
                        return True

                # Handle tool calls
                if response.tool_calls:
                    # Build assistant message with tool use for internal tracking
                    assistant_content = []
                    if response.content:
                        assistant_content.append({
                            'type': 'text',
                            'text': response.content
                        })

                    for tool_call in response.tool_calls:
                        assistant_content.append({
                            'type': 'tool_use',
                            'id': tool_call.id,
                            'name': tool_call.name,
                            'input': tool_call.input
                        })

                    self.messages.append({
                        'role': 'assistant',
                        'content': assistant_content
                    })

                    # Execute tools and collect results
                    tool_results = []
                    for tool_call in response.tool_calls:
                        result = self.execute_tool(tool_call.name, tool_call.input)

                        # Emit tool result for daemon
                        self.output.tool_result(
                            tool_call.name,
                            result.output,
                            result.is_error,
                            tool_call.id
                        )

                        tool_results.append({
                            'type': 'tool_result',
                            'tool_use_id': tool_call.id,
                            'content': result.output,
                            'is_error': result.is_error
                        })

                    # Add tool results to messages
                    self.messages.append({
                        'role': 'user',
                        'content': tool_results
                    })

                    # Check for completion AFTER tools executed
                    if response.content and self.config.completion_marker in response.content:
                        # Tools executed, now we can complete
                        self._emit_result(True)
                        return True

                # Check stop reason
                if response.stop_reason == 'end_turn' and not response.tool_calls:
                    self._emit_result(True)
                    return True

                if response.stop_reason == 'max_tokens':
                    self.output.error("Response truncated due to max tokens")
                    self._emit_result(False)
                    return False

            except Exception as e:
                self.output.error(str(e), traceback.format_exc() if self.verbose else None)
                self._emit_result(False)
                return False

        # Max iterations reached
        self.output.error(f"Max iterations ({max_iterations}) reached")
        self._emit_result(False)
        return False

    def _emit_result(self, success: bool):
        """Emit final result with usage stats.

        Args:
            success: Whether task completed successfully
        """
        self.output.result(
            usage={
                'input_tokens': self.total_input_tokens,
                'output_tokens': self.total_output_tokens,
            },
            success=success
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HeroAgent - Coding Agent for CodeHero',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-p', '--prompt',
        required=True,
        help='The task/prompt to execute'
    )

    parser.add_argument(
        '--model',
        default=None,
        help='Model name (opus/sonnet/haiku or provider-specific)'
    )

    parser.add_argument(
        '--provider',
        default=None,
        help='AI provider (anthropic/gemini/grok/openai/ollama)'
    )

    parser.add_argument(
        '--dangerously-skip-permissions',
        action='store_true',
        help='Skip all permission prompts (autonomous mode)'
    )

    parser.add_argument(
        '--output-format',
        choices=['stream-json', 'text', 'print'],
        default='stream-json',
        help='Output format (default: stream-json)'
    )

    parser.add_argument(
        '--print',
        action='store_true',
        dest='simple_print',
        help='Simple text output (equivalent to --output-format print)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--cwd',
        default=None,
        help='Working directory'
    )

    parser.add_argument(
        '--config',
        default=None,
        help='Path to config file'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'HeroAgent {__version__}'
    )

    args = parser.parse_args()

    # Load config
    config = get_config(args.config)

    # Determine output format
    output_format = 'print' if args.simple_print else args.output_format

    # Create output handler
    output = StreamOutput(
        output_format=output_format,
        verbose=args.verbose
    )

    # Determine provider and model
    provider_name = args.provider or config.default_provider
    model = args.model or config.default_model

    # Set working directory
    cwd = args.cwd
    if cwd:
        cwd = os.path.abspath(os.path.expanduser(cwd))
        if not os.path.exists(cwd):
            output.error(f"Working directory not found: {cwd}")
            sys.exit(1)
        os.chdir(cwd)

    # Create and run agent
    try:
        agent = HeroAgent(
            config=config,
            output=output,
            skip_permissions=args.dangerously_skip_permissions,
            cwd=cwd,
            verbose=args.verbose
        )

        success = agent.run(args.prompt, provider_name, model)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        output.error("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        output.error(str(e), traceback.format_exc() if args.verbose else None)
        sys.exit(1)


if __name__ == '__main__':
    main()

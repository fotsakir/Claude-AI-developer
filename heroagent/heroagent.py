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

# Global context file path
GLOBAL_CONTEXT_FILE = '/etc/codehero/global-context.md'

def load_global_context():
    """Load global context from file"""
    try:
        with open(GLOBAL_CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load global context: {e}", file=sys.stderr)
        return ""

# HeroAgent-specific header (execution rules, tools)
HEROAGENT_HEADER = """You are HeroAgent, a coding assistant that EXECUTES tasks using tools.

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
- Screenshot: FULL PAGE VERIFICATION - takes screenshots AND captures console errors + failed requests

=== COMPLETION ===

When done say "TASK COMPLETED" with:
- Files created/modified
- console_errors=0, failed_requests=0
- Server logs: clean
- Preview URL

DO NOT mark complete if errors exist!
"""

def get_system_prompt():
    """Get combined system prompt: HeroAgent header + Global Context"""
    global_context = load_global_context()
    if global_context:
        return f"{HEROAGENT_HEADER}\n\n---\n\n# GLOBAL CONTEXT (Coding Standards)\n\n{global_context}"
    return HEROAGENT_HEADER

# Legacy alias for compatibility
SYSTEM_PROMPT = None  # Will be set dynamically



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
        self.provider.set_system_prompt(get_system_prompt())

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

"""
HeroAgent OpenAI Provider

OpenAI GPT models via OpenAI API.
Supports both Chat Completions API and Responses API (for pro models).
"""

import json
from typing import Dict, List, Any, Optional, Generator

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from .base import BaseProvider, Response, ToolCall


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider."""

    # Models that require the Responses API instead of Chat Completions
    RESPONSES_API_MODELS = [
        'gpt-5-pro', 'gpt-5.1-pro', 'gpt-5.2-pro',
        'o1-pro', 'o3-pro', 'o4-pro'
    ]

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            **kwargs: Additional options
        """
        super().__init__(api_key, **kwargs)

        if not HAS_OPENAI:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = kwargs.get('model', 'gpt-4o')

    def _is_responses_api_model(self) -> bool:
        """Check if current model requires the Responses API."""
        return any(self.model.startswith(m) for m in self.RESPONSES_API_MODELS)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Response:
        """Send messages and get a response."""
        if self._is_responses_api_model():
            return self._chat_responses_api(messages, tools, max_tokens, **kwargs)
        else:
            return self._chat_completions_api(messages, tools, max_tokens, **kwargs)

    def _chat_completions_api(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Response:
        """Use Chat Completions API for standard models."""
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages)

        # Add system message
        if self.system_prompt:
            openai_messages.insert(0, {
                'role': 'system',
                'content': self.system_prompt
            })

        # Prepare request
        request_kwargs = {
            'model': self.model,
            'max_completion_tokens': max_tokens,
            'messages': openai_messages,
        }

        if tools:
            request_kwargs['tools'] = self._convert_tools_chat(tools)
            request_kwargs['tool_choice'] = 'auto'

        # Make request
        response = self.client.chat.completions.create(**request_kwargs)

        return self._parse_chat_response(response)

    def _chat_responses_api(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Response:
        """Use Responses API for pro models."""
        # Build input from messages
        input_text = self._build_responses_input(messages)

        # Prepare request
        request_kwargs = {
            'model': self.model,
            'input': input_text,
        }

        if max_tokens:
            request_kwargs['max_output_tokens'] = max_tokens

        if tools:
            request_kwargs['tools'] = self._convert_tools_responses(tools)

        if self.system_prompt:
            request_kwargs['instructions'] = self.system_prompt

        # Make request
        response = self.client.responses.create(**request_kwargs)

        return self._parse_responses_response(response)

    def _build_responses_input(self, messages: List[Dict[str, Any]]) -> str:
        """Build input string for Responses API from messages."""
        parts = []
        for msg in messages:
            role = msg['role']
            content = msg['content']

            if isinstance(content, str):
                if role == 'user':
                    parts.append(content)
                elif role == 'assistant':
                    parts.append(f"Assistant: {content}")
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text = item.get('text', '')
                        if role == 'user':
                            parts.append(text)
                        elif role == 'assistant':
                            parts.append(f"Assistant: {text}")

        # Return the last user message or full conversation
        return '\n\n'.join(parts) if parts else ''

    def stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream messages and yield events."""
        if self._is_responses_api_model():
            yield from self._stream_responses_api(messages, tools, max_tokens, **kwargs)
        else:
            yield from self._stream_completions_api(messages, tools, max_tokens, **kwargs)

    def _stream_completions_api(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream using Chat Completions API."""
        openai_messages = self._convert_messages(messages)

        if self.system_prompt:
            openai_messages.insert(0, {
                'role': 'system',
                'content': self.system_prompt
            })

        request_kwargs = {
            'model': self.model,
            'max_completion_tokens': max_tokens,
            'messages': openai_messages,
            'stream': True,
        }

        if tools:
            request_kwargs['tools'] = self._convert_tools_chat(tools)
            request_kwargs['tool_choice'] = 'auto'

        stream = self.client.chat.completions.create(**request_kwargs)

        current_tool_calls = {}

        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue

            delta = choice.delta

            # Text content
            if delta.content:
                yield {
                    'type': 'text_delta',
                    'text': delta.content,
                }

            # Tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.index not in current_tool_calls:
                        current_tool_calls[tc.index] = {
                            'id': tc.id or f"call_{tc.index}",
                            'name': tc.function.name if tc.function else '',
                            'arguments': ''
                        }
                    if tc.function and tc.function.arguments:
                        current_tool_calls[tc.index]['arguments'] += tc.function.arguments

            # End of stream
            if choice.finish_reason:
                break

        # Emit tool calls
        for tc_data in current_tool_calls.values():
            try:
                args = json.loads(tc_data['arguments']) if tc_data['arguments'] else {}
            except json.JSONDecodeError:
                args = {}
            yield {
                'type': 'tool_use',
                'id': tc_data['id'],
                'name': tc_data['name'],
                'input': args,
            }

        yield {
            'type': 'final',
            'stop_reason': 'end_turn',
            'usage': {'input_tokens': 0, 'output_tokens': 0}
        }

    def _stream_responses_api(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream using Responses API."""
        input_text = self._build_responses_input(messages)

        request_kwargs = {
            'model': self.model,
            'input': input_text,
            'stream': True,
        }

        if max_tokens:
            request_kwargs['max_output_tokens'] = max_tokens

        if tools:
            request_kwargs['tools'] = self._convert_tools_responses(tools)

        if self.system_prompt:
            request_kwargs['instructions'] = self.system_prompt

        stream = self.client.responses.stream(**request_kwargs)

        with stream as response_stream:
            for event in response_stream:
                if hasattr(event, 'type'):
                    if event.type == 'response.output_text.delta':
                        yield {
                            'type': 'text_delta',
                            'text': event.delta,
                        }
                    elif event.type == 'response.function_call_arguments.done':
                        try:
                            args = json.loads(event.arguments) if event.arguments else {}
                        except json.JSONDecodeError:
                            args = {}
                        yield {
                            'type': 'tool_use',
                            'id': event.call_id if hasattr(event, 'call_id') else f"call_{id(event)}",
                            'name': event.name if hasattr(event, 'name') else 'unknown',
                            'input': args,
                        }

        yield {
            'type': 'final',
            'stop_reason': 'end_turn',
            'usage': {'input_tokens': 0, 'output_tokens': 0}
        }

    def supports_tools(self) -> bool:
        return True

    def supports_streaming(self) -> bool:
        return True

    def _convert_tools_chat(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Chat Completions API format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                'type': 'function',
                'function': {
                    'name': tool['name'],
                    'description': tool.get('description', ''),
                    'parameters': tool.get('input_schema', {'type': 'object', 'properties': {}})
                }
            })
        return openai_tools

    def _convert_tools_responses(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Responses API format."""
        responses_tools = []
        for tool in tools:
            responses_tools.append({
                'type': 'function',
                'name': tool['name'],
                'description': tool.get('description', ''),
                'parameters': tool.get('input_schema', {'type': 'object', 'properties': {}})
            })
        return responses_tools

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to OpenAI Chat Completions format."""
        openai_messages = []

        for msg in messages:
            role = msg['role']
            content = msg['content']

            if isinstance(content, str):
                openai_messages.append({
                    'role': role,
                    'content': content
                })
            elif isinstance(content, list):
                # Handle tool use and results
                text_parts = []
                tool_calls = []
                tool_results = []

                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                        elif item.get('type') == 'tool_use':
                            tool_calls.append({
                                'id': item.get('id', f"call_{len(tool_calls)}"),
                                'type': 'function',
                                'function': {
                                    'name': item.get('name'),
                                    'arguments': json.dumps(item.get('input', {}))
                                }
                            })
                        elif item.get('type') == 'tool_result':
                            tool_results.append({
                                'role': 'tool',
                                'tool_call_id': item.get('tool_use_id'),
                                'content': item.get('content', '')
                            })

                if role == 'assistant' and tool_calls:
                    openai_messages.append({
                        'role': 'assistant',
                        'content': '\n'.join(text_parts) if text_parts else None,
                        'tool_calls': tool_calls
                    })
                elif tool_results:
                    openai_messages.extend(tool_results)
                elif text_parts:
                    openai_messages.append({
                        'role': role,
                        'content': '\n'.join(text_parts)
                    })

        return openai_messages

    def _parse_chat_response(self, response) -> Response:
        """Parse Chat Completions API response."""
        message = response.choices[0].message

        content_text = message.content or ""
        tool_calls = []

        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    input=args,
                ))

        stop_reason = 'end_turn'
        if response.choices[0].finish_reason == 'tool_calls':
            stop_reason = 'tool_use'
        elif response.choices[0].finish_reason == 'length':
            stop_reason = 'max_tokens'

        return Response(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage={
                'input_tokens': response.usage.prompt_tokens if response.usage else 0,
                'output_tokens': response.usage.completion_tokens if response.usage else 0,
            }
        )

    def _parse_responses_response(self, response) -> Response:
        """Parse Responses API response."""
        content_text = ""
        tool_calls = []

        for item in response.output:
            if item.type == 'message':
                for content in item.content:
                    if hasattr(content, 'text'):
                        content_text += content.text
            elif item.type == 'function_call':
                try:
                    args = json.loads(item.arguments) if item.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(
                    id=item.id if hasattr(item, 'id') else f"call_{len(tool_calls)}",
                    name=item.name,
                    input=args,
                ))

        stop_reason = 'end_turn'
        if tool_calls:
            stop_reason = 'tool_use'

        return Response(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage={
                'input_tokens': response.usage.input_tokens if response.usage else 0,
                'output_tokens': response.usage.output_tokens if response.usage else 0,
            }
        )

    def validate_config(self) -> bool:
        if not self.client.api_key:
            raise ValueError("OpenAI API key not configured")
        return True

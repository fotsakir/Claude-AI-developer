"""
HeroAgent Gemini Provider

Google Gemini models via the new google-genai SDK.
"""

import json
from typing import Dict, List, Any, Optional, Generator

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from .base import BaseProvider, Response, ToolCall


class GeminiProvider(BaseProvider):
    """Google Gemini provider using new google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Gemini provider.

        Args:
            api_key: Google API key
            **kwargs: Additional options
        """
        super().__init__(api_key, **kwargs)

        if not HAS_GEMINI:
            raise ImportError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = kwargs.get('model', 'gemini-2.0-flash')

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Response:
        """Send messages and get a response."""

        # Convert messages to Gemini format
        gemini_contents = self._convert_messages(messages)

        # Build config
        config_dict = {
            'max_output_tokens': max_tokens,
        }

        if self.system_prompt:
            config_dict['system_instruction'] = self.system_prompt

        if tools:
            config_dict['tools'] = self._convert_tools(tools)

        config = types.GenerateContentConfig(**config_dict)

        # Generate response
        response = self.client.models.generate_content(
            model=self.model,
            contents=gemini_contents,
            config=config,
        )

        return self._parse_response(response)

    def stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream messages and yield events."""

        gemini_contents = self._convert_messages(messages)

        config_dict = {
            'max_output_tokens': max_tokens,
        }

        if self.system_prompt:
            config_dict['system_instruction'] = self.system_prompt

        if tools:
            config_dict['tools'] = self._convert_tools(tools)

        config = types.GenerateContentConfig(**config_dict)

        # Use streaming endpoint
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=gemini_contents,
            config=config,
        ):
            if chunk.text:
                yield {
                    'type': 'text_delta',
                    'text': chunk.text,
                }

            # Check for tool calls in chunk
            if hasattr(chunk, 'candidates') and chunk.candidates:
                for candidate in chunk.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                yield {
                                    'type': 'tool_use',
                                    'id': f"call_{id(part)}",
                                    'name': part.function_call.name,
                                    'input': dict(part.function_call.args) if part.function_call.args else {},
                                }

        # Get usage if available
        input_tokens = 0
        output_tokens = 0

        yield {
            'type': 'final',
            'stop_reason': 'end_turn',
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
            }
        }

    def supports_tools(self) -> bool:
        return True

    def supports_streaming(self) -> bool:
        return True

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List:
        """Convert tools to Gemini format."""
        function_declarations = []
        for tool in tools:
            func_decl = types.FunctionDeclaration(
                name=tool['name'],
                description=tool.get('description', ''),
                parameters=tool.get('input_schema', {'type': 'object', 'properties': {}})
            )
            function_declarations.append(func_decl)

        return [types.Tool(function_declarations=function_declarations)]

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List:
        """Convert messages to Gemini format."""
        gemini_contents = []

        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'model'
            content = msg['content']

            if isinstance(content, str):
                gemini_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content)]
                    )
                )
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            parts.append(types.Part.from_text(text=item.get('text', '')))
                        elif item.get('type') == 'tool_use':
                            # Function call from assistant
                            parts.append(types.Part.from_function_call(
                                name=item.get('name', 'unknown'),
                                args=item.get('input', {}) or {}
                            ))
                        elif item.get('type') == 'tool_result':
                            # Function response
                            parts.append(types.Part.from_function_response(
                                name=item.get('tool_use_id', 'tool'),
                                response={'result': str(item.get('content', ''))}
                            ))
                    elif isinstance(item, str):
                        parts.append(types.Part.from_text(text=item))

                if parts:
                    gemini_contents.append(
                        types.Content(role=role, parts=parts)
                    )

        return gemini_contents

    def _parse_response(self, response) -> Response:
        """Parse Gemini response."""
        content_text = ""
        tool_calls = []

        try:
            # Get text content
            if hasattr(response, 'text'):
                content_text = response.text or ""

            # Check for function calls
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                tool_calls.append(ToolCall(
                                    id=f"call_{len(tool_calls)}",
                                    name=fc.name,
                                    input=dict(fc.args) if fc.args else {},
                                ))
        except Exception as e:
            # Fallback
            if hasattr(response, 'text'):
                content_text = response.text or ""

        stop_reason = 'end_turn'
        if tool_calls:
            stop_reason = 'tool_use'

        # Get usage metadata
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            um = response.usage_metadata
            input_tokens = getattr(um, 'prompt_token_count', 0) or 0
            output_tokens = getattr(um, 'candidates_token_count', 0) or 0

        return Response(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage={
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
            }
        )

    def validate_config(self) -> bool:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        return True

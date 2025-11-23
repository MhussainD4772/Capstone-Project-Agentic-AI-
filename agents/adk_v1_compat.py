"""
ADK v1 Compatibility Layer

This module provides a compatibility layer for ADK v1 loop.Loop interface
when the loop module is not directly available in the installed package.
"""

from typing import AsyncGenerator, Any, Optional
from google.genai import types
import google.generativeai as genai
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import BaseAgent
from google.adk.events import Event
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure Google Generative AI with API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


class Context:
    """Compatibility Context class matching loop.Context interface."""
    
    def __init__(self, last_user_message: types.Content, llm, response_callback):
        self.last_user_message = last_user_message
        self.llm = llm
        self._response_callback = response_callback
        self._response_value = None
    
    def response(self, text: str):
        """Create a response - returns the text so it can be yielded."""
        self._response_callback(text)
        self._response_value = text
        return text


class Loop:
    """Compatibility Loop base class matching loop.Loop interface."""
    
    async def run(self, ctx: Context) -> AsyncGenerator[Any, None]:
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")


class LoopAgentAdapter(BaseAgent):
    """
    Adapter that wraps a Loop class to make it work as a BaseAgent.
    This allows Loop classes to be used with Runner.
    """
    
    def __init__(self, loop_class, name: str, description: str = ""):
        """
        Initialize the adapter.
        
        Args:
            loop_class: The Loop class to wrap
            name: Name for the agent
            description: Description for the agent
        """
        super().__init__(name=name, description=description)
        self._loop_class = loop_class
        self._loop_instance = None
    
    async def run_async(self, parent_context) -> AsyncGenerator[Event, None]:
        """
        Run the wrapped Loop as a BaseAgent.
        
        This method:
        1. Extracts the last user message from the context
        2. Creates a Context object for the Loop
        3. Creates an LLM wrapper
        4. Calls the Loop's run method
        5. Converts Loop responses to Events
        """
        # Get the last user message from session
        session = parent_context.session
        last_user_message = None
        
        # Find the last user message in session events
        if hasattr(session, 'events') and session.events:
            for event in reversed(session.events):
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'role') and event.content.role == 'user':
                        last_user_message = event.content
                        break
        
        # If no user message found, try to get from new_message in context
        if not last_user_message:
            if hasattr(parent_context, 'new_message') and parent_context.new_message:
                last_user_message = parent_context.new_message
            elif hasattr(parent_context, 'state') and parent_context.state:
                # Create message from state
                import json
                state = parent_context.state
                if isinstance(state, dict):
                    last_user_message = types.Content(
                        role="user",
                        parts=[types.Part(text=json.dumps(state))]
                    )
        
        if not last_user_message:
            last_user_message = types.Content(
                role="user",
                parts=[types.Part(text="")]
            )
        
        # Create LLM wrapper
        class LLMWrapper:
            def __init__(self, model_name: str = "gemini-2.0-flash"):
                self.model_name = model_name
                self._model = None
            
            async def complete(self, prompt: str, model: Optional[str] = None):
                """Complete a prompt using the LLM."""
                model_name = model or self.model_name
                if self._model is None or model_name != self.model_name:
                    self._model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                
                result = await self._model.generate_content_async(prompt)
                return type('Result', (), {'text': result.text})()
        
        llm = LLMWrapper()
        
        # Track responses from the loop
        final_response = None
        
        # Response callback that captures the response
        def response_callback(text: str):
            nonlocal final_response
            final_response = text
        
        # Create context for Loop
        ctx = Context(
            last_user_message=last_user_message,
            llm=llm,
            response_callback=response_callback
        )
        
        # Instantiate loop if not already done
        if self._loop_instance is None:
            self._loop_instance = self._loop_class()
        
        # Run the loop and collect responses
        async for response in self._loop_instance.run(ctx):
            # The loop yields responses (strings) from ctx.response()
            if isinstance(response, str):
                final_response = response
                # Also update via callback
                response_callback(response)
            elif hasattr(response, 'content'):
                # If it's already an event-like object, yield it
                yield response
        
        # Yield the final response as an event
        # Use final_response or the one from callback
        response_text = final_response or ctx._response_value
        if response_text:
            from google.adk.events import Event as ADKEvent
            yield ADKEvent(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=response_text)]
                ),
                author="agent"
            )


# Make it importable as google.adk.loop
import sys
import types as py_types

# Create a mock module
loop_module = py_types.ModuleType('google.adk.loop')
loop_module.Loop = Loop
loop_module.Context = Context
# Runner is the same as google.adk.runners.Runner
loop_module.Runner = Runner
# Add adapter for converting Loop to BaseAgent
loop_module.LoopAgentAdapter = LoopAgentAdapter

# Add to sys.modules so "from google.adk import loop" works
sys.modules['google.adk.loop'] = loop_module

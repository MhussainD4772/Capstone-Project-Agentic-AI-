"""Orchestrator agent module.

This module implements the QA Sentinel Orchestrator that coordinates the full
multi-agent pipeline for processing user stories through planning, test case generation,
and validation stages.
"""

from typing import Dict, List, Any

import json

# Import compatibility layer first
import agents.adk_v1_compat  # noqa: F401

from google.adk import loop
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.story_planner_agent import StoryPlannerLoop
from agents.testcase_generator_agent import TestCaseGeneratorLoop
from agents.global_validator_agent import GlobalValidatorLoop
from memory.qa_style_memory import QAStyleMemory
from memory.session_store import SessionStore


class QASentinelOrchestrator:
    """
    Orchestrator that coordinates the full multi-agent QA pipeline.

    Responsibilities:
    1. Manage session state across the pipeline
    2. Coordinate StoryPlannerLoop, TestCaseGeneratorLoop, and GlobalValidatorLoop
    3. Retrieve similar examples from memory to inform test case generation
    4. Save results to both session store and style memory
    5. Return a consolidated result dictionary

    This class does not call LLMs directly; it just coordinates ADK agents.
    """

    def __init__(self, memory: QAStyleMemory, session_store: SessionStore):
        """
        Initialize the orchestrator with memory and session store.

        Args:
            memory: QAStyleMemory instance for storing QA examples
            session_store: SessionStore instance for tracking sessions
        """
        self.memory = memory
        self.session_store = session_store
        # Create session service for ADK runners
        self.session_service = InMemorySessionService()

    def _extract_json_from_event(self, event: Any, agent_name: str) -> Dict[str, Any]:
        """
        Extract JSON output from an ADK event with robust error handling.

        Args:
            event: ADK event object
            agent_name: Name of the agent for error messages

        Returns:
            Parsed JSON dictionary

        Raises:
            RuntimeError: If event structure is invalid or JSON parsing fails
        """
        if not hasattr(event, "content") or event.content is None:
            raise RuntimeError(f"{agent_name} returned event without content")

        if not hasattr(event.content, "parts") or event.content.parts is None:
            raise RuntimeError(f"{agent_name} returned event without content.parts")

        if len(event.content.parts) == 0:
            raise RuntimeError(f"{agent_name} returned event with empty parts array")

        first_part = event.content.parts[0]
        if not hasattr(first_part, "text"):
            raise RuntimeError(f"{agent_name} returned event part without text attribute")

        try:
            return json.loads(first_part.text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"{agent_name} returned non-JSON output: {e}") from e
        except Exception as e:
            raise RuntimeError(f"{agent_name} returned invalid JSON: {e}") from e

    async def run_pipeline(
        self,
        session_id: str,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        qa_context: str,
    ) -> Dict[str, Any]:
        """
        Run the complete QA pipeline for a user story.

        High-level flow:
        1. Start session in session_store
        2. Run StoryPlannerLoop to generate scenarios
        3. Retrieve similar examples from memory
        4. Run TestCaseGeneratorLoop to generate test cases
        5. Run GlobalValidatorLoop to validate the entire pipeline
        6. Save results to session_store and memory
        7. Return consolidated results
        """
        # 1. Start session
        try:
            self.session_store.start_session(session_id, title, qa_context)
        except ValueError as e:
            raise ValueError(f"Failed to start session {session_id}: {e}")

        try:
            # 2. Run StoryPlannerLoop (Planner)
            # Wrap Loop in adapter to make it BaseAgent-compatible
            planner_agent = loop.LoopAgentAdapter(
                loop_class=StoryPlannerLoop,
                name="StoryPlannerLoop",
                description="Generates structured features and scenarios from user stories"
            )
            planner_runner = loop.Runner(
                agent=planner_agent,
                app_name="agents",
                session_service=self.session_service
            )

            planner_input = {
                "title": title,
                "description": description,
                "acceptance_criteria": acceptance_criteria,
                "qa_context": qa_context,
            }

            planner_message = types.Content(
                role="user",
                parts=[types.Part(text=json.dumps(planner_input))],
            )

            # Create session first
            planner_session_id = f"{session_id}-planner"
            await self.session_service.create_session(
                app_name="agents",
                user_id="qa-sentinel",
                session_id=planner_session_id,
                state=planner_input
            )

            planner_output = None
            async for event in planner_runner.run_async(
                user_id="qa-sentinel",
                session_id=planner_session_id,
                new_message=planner_message,
            ):
                if hasattr(event, "is_final_response") and event.is_final_response():
                    planner_output = self._extract_json_from_event(event, "StoryPlannerLoop")
                    break

            if planner_output is None:
                raise RuntimeError("StoryPlannerLoop did not return valid output")

            self.session_store.save_stage_output(session_id, "planner_output", planner_output)

            # 3. Retrieve similar examples from memory
            similar_examples = self.memory.get_similar_examples(title, top_k=3)

            # 4. Run TestCaseGeneratorLoop (Test Case Generator)
            # Wrap Loop in adapter to make it BaseAgent-compatible
            testcase_agent = loop.LoopAgentAdapter(
                loop_class=TestCaseGeneratorLoop,
                name="TestCaseGeneratorLoop",
                description="Generates test cases from planner output"
            )
            testcase_runner = loop.Runner(
                agent=testcase_agent,
                app_name="agents",
                session_service=self.session_service
            )

            testcase_input = {
                "planner_output": planner_output,
                "qa_context": qa_context,
                "similar_examples": similar_examples,
            }

            testcase_message = types.Content(
                role="user",
                parts=[types.Part(text=json.dumps(testcase_input))],
            )

            # Create session first
            testcase_session_id = f"{session_id}-testcase"
            await self.session_service.create_session(
                app_name="agents",
                user_id="qa-sentinel",
                session_id=testcase_session_id,
                state=testcase_input
            )

            testcase_output = None
            async for event in testcase_runner.run_async(
                user_id="qa-sentinel",
                session_id=testcase_session_id,
                new_message=testcase_message,
            ):
                if hasattr(event, "is_final_response") and event.is_final_response():
                    testcase_output = self._extract_json_from_event(
                        event, "TestCaseGeneratorLoop"
                    )
                    break

            if testcase_output is None:
                raise RuntimeError("TestCaseGeneratorLoop did not return valid output")

            self.session_store.save_stage_output(session_id, "testcase_output", testcase_output)

            # 5. Run GlobalValidatorLoop (Global Validator)
            # Wrap Loop in adapter to make it BaseAgent-compatible
            validation_agent = loop.LoopAgentAdapter(
                loop_class=GlobalValidatorLoop,
                name="GlobalValidatorLoop",
                description="Validates entire QA pipeline for consistency and quality"
            )
            validation_runner = loop.Runner(
                agent=validation_agent,
                app_name="agents",
                session_service=self.session_service
            )

            validation_input = {
                "planner_output": planner_output,
                "testcase_output": testcase_output,
                "qa_context": qa_context,
            }

            validation_message = types.Content(
                role="user",
                parts=[types.Part(text=json.dumps(validation_input))],
            )

            # Create session first
            validation_session_id = f"{session_id}-validation"
            await self.session_service.create_session(
                app_name="agents",
                user_id="qa-sentinel",
                session_id=validation_session_id,
                state=validation_input
            )

            global_validation_output = None
            async for event in validation_runner.run_async(
                user_id="qa-sentinel",
                session_id=validation_session_id,
                new_message=validation_message,
            ):
                if hasattr(event, "is_final_response") and event.is_final_response():
                    global_validation_output = self._extract_json_from_event(
                        event, "GlobalValidatorLoop"
                    )
                    break

            if global_validation_output is None:
                raise RuntimeError("GlobalValidatorLoop did not return valid output")

            self.session_store.save_stage_output(
                session_id,
                "global_validation_output",
                global_validation_output,
            )

            # 6. Save this story into QAStyleMemory
            self.memory.save_example(
                story_id=session_id,
                title=title,
                acceptance_criteria=acceptance_criteria,
                planner_output=planner_output,
                testcase_output=testcase_output,
                qa_context=qa_context,
            )

            # 7. Return final consolidated result
            return {
                "session_id": session_id,
                "title": title,
                "qa_context": qa_context,
                "planner_output": planner_output,
                "testcase_output": testcase_output,
                "global_validation_output": global_validation_output,
            }

        except Exception as e:
            raise RuntimeError(f"Pipeline execution failed at stage: {e}") from e

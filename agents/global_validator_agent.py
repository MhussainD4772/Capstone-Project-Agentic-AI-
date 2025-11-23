"""
Global Validator Loop — ADK v1 compatible

This module implements the Global QA Validator Agent as a Loop, using the
google.adk.loop.Loop interface (the current ADK standard).

No @agent decorator is used (removed in ADK v1).
"""

# Import compatibility layer first
import agents.adk_v1_compat  # noqa: F401

from google.adk import loop
from google.genai import types
import json


class GlobalValidatorLoop(loop.Loop):
    """
    Global Validator Loop — validates entire QA pipeline.

    Input (JSON text):
        {
            "planner_output": {...},
            "testcase_output": {...},
            "qa_context": "..."
        }

    Output (JSON text):
        {
            "valid": true/false,
            "errors": [...],
            "warnings": [...]
        }
    """

    async def run(self, ctx: loop.Context):
        """Main entrypoint for the loop."""
        # Extract user message
        msg = ctx.last_user_message
        if not msg or not msg.parts:
            yield ctx.response("Error: No input provided.")
            return

        try:
            input_data = json.loads(msg.parts[0].text)
        except Exception:
            yield ctx.response("Error: Input must be JSON.")
            return

        planner_output = input_data.get("planner_output", {})
        testcase_output = input_data.get("testcase_output", {})
        qa_context = input_data.get("qa_context", "")

        # Construct the LLM prompt
        prompt = f"""
You are a senior QA validator evaluating the ENTIRE QA pipeline for consistency, completeness, and quality.

Validate these cross-agent rules:
1. Coverage Completeness: Every scenario from planner_output.scenarios must map to ≥1 test case. No missing or orphan scenarios.
2. Step Quality: Every test case must have ≥1 Given, ≥1 When, ≥1 Then. Steps must be clear, actionable, not ambiguous.
3. Expected Result Quality: Expected results must be specific and testable. No vague phrases like 'should work fine', 'expected to work'.
4. Duplicate Detection: No duplicate test cases with same title or logically identical steps.
5. Edge Case / Risk Alignment: Edge cases must be meaningful and related to the story. Bug-risk insights must come from planner scenarios or logical domain reasoning.
6. Consistency Across Agents: Titles, scenarios, IDs, and flows must match planner_output. No contradictions between planner_output features and generated test cases.
7. QA Context Alignment: If qa_context emphasizes patterns (e.g., 'negative testing', 'security', 'UX'), verify these preferences appear in test cases or edge cases.

DO NOT modify planner or test case outputs. Only evaluate and report.
DO NOT output Python. DO NOT explain. Return JSON only.

Output strict JSON structure:
{{
  "valid": true/false,
  "errors": [...],
  "warnings": [...]
}}

Planner Output: {json.dumps(planner_output, indent=2)}
Test Case Output: {json.dumps(testcase_output, indent=2)}
QA Context: {qa_context}
        """

        # Call the model
        result = await ctx.llm.complete(
            prompt=prompt,
            model="gemini-2.0-flash"
        )

        text = result.text
        # Strip markdown code blocks if present
        if text.strip().startswith("```"):
            # Remove opening ```json or ```
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            # Remove closing ```
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        
        try:
            parsed = json.loads(text)
        except Exception:
            # If LLM output is not valid JSON, wrap it as an error
            parsed = {"error": "Model returned invalid JSON", "raw_output": text, "valid": False}

        # Return as final response
        yield ctx.response(json.dumps(parsed))

"""
Test Case Generator Loop — ADK v1 compatible

This module implements the TestCase Generator Agent as a Loop, using the
google.adk.loop.Loop interface (the current ADK standard).

No @agent decorator is used (removed in ADK v1).
"""

# Import compatibility layer first
import agents.adk_v1_compat  # noqa: F401

from google.adk import loop
from google.genai import types
import json


class TestCaseGeneratorLoop(loop.Loop):
    """
    Test Case Generator Loop — generates test cases from planner output.

    Input (JSON text):
        {
            "planner_output": {...},
            "qa_context": "...",
            "similar_examples": [...]
        }

    Output (JSON text):
        {
            "test_cases": [...],
            "edge_cases": [...],
            "bug_risks": [...],
            "planner_output": {...}
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
        qa_context = input_data.get("qa_context", "")
        similar_examples = input_data.get("similar_examples", [])

        # Construct the LLM prompt
        prompt = f"""
You are a senior QA test case generator.

Convert planner_output scenarios into test cases using hybrid QA format.
For EACH scenario, generate 1-3 test cases.

Test case format: Title, Preconditions (array), Steps (Given/When/Then strings), Expected Result.
Use qa_context to influence style (e.g., if negative testing preferred, include more edge cases).

ID rules: test_cases (TC-1, TC-2...), edge_cases (EC-1, EC-2...), bug_risks (BR-1, BR-2...).
Steps MUST be valid Gherkin style: 'Given ...', 'When ...', 'Then ...'.
Each test case must include at least one 'Given', one 'When', and one 'Then' step in the steps array.
For every scenario_id in planner_output.scenarios, at least one test case must clearly reference that scenario in the title or steps.

Include the original planner_output JSON under the key 'planner_output' so that validators can access planner_output.scenarios.

DO NOT output Python. DO NOT explain. Return JSON only.

Output strict JSON structure:
{{
  "test_cases": [
    {{
      "id": "TC-1",
      "title": "",
      "preconditions": [],
      "steps": ["Given ...", "When ...", "Then ..."],
      "expected_result": ""
    }}
  ],
  "edge_cases": [
    {{
      "id": "EC-1",
      "description": ""
    }}
  ],
  "bug_risks": [
    {{
      "id": "BR-1",
      "description": ""
    }}
  ],
  "planner_output": <ORIGINAL_PLANNER_OUTPUT_JSON>
}}

Planner Output: {json.dumps(planner_output, indent=2)}
QA Context: {qa_context}
Similar Examples: {json.dumps(similar_examples, indent=2) if similar_examples else "None"}
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
            # Ensure planner_output is included
            if "planner_output" not in parsed:
                parsed["planner_output"] = planner_output
        except Exception:
            # If LLM output is not valid JSON, wrap it as an error
            parsed = {"error": "Model returned invalid JSON", "raw_output": text}

        # Return as final response
        yield ctx.response(json.dumps(parsed))

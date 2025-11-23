"""
Story Planner Loop — ADK v1 compatible

This module implements the Story Planner Agent as a Loop, using the
google.adk.loop.Loop interface (the current ADK standard).

No @agent decorator is used (removed in ADK v1).
"""

# Import compatibility layer first
import agents.adk_v1_compat  # noqa: F401

from google.adk import loop
from google.genai import types
import json


class StoryPlannerLoop(loop.Loop):
    """
    Story Planner Loop — generates structured features + scenarios.

    Input (JSON text):
        {
            "title": "...",
            "description": "...",
            "acceptance_criteria": [...],
            "qa_context": "..."
        }

    Output (JSON text):
        {
            "features": [...],
            "scenarios": [...],
            "notes": [...],
            "acceptance_criteria_input": [...]
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

        title = input_data.get("title", "")
        description = input_data.get("description", "")
        ac_list = input_data.get("acceptance_criteria", [])
        qa_context = input_data.get("qa_context", "")

        # Construct the LLM prompt
        prompt = f"""
You are a senior QA analyst.

Break the story into:
- 3–8 features
- Scenarios (SC-1, SC-2, ...)
- Notes
Each acceptance criteria must be linked to at least one scenario.

Return ONLY strict JSON:
{{
  "features": [...],
  "scenarios": [
      {{
          "scenario_id": "SC-1",
          "title": "",
          "acceptance_criteria": "",
          "tags": []
      }}
  ],
  "notes": [...],
  "acceptance_criteria_input": [...]
}}

Story Title: {title}
Description: {description}
Acceptance Criteria: {ac_list}
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
            parsed = {"error": "Model returned invalid JSON", "raw_output": text}

        # Return as final response
        yield ctx.response(json.dumps(parsed))

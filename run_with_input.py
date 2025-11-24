"""Simple script to run QA Sentinel with input from a JSON file.

Usage:
    python run_with_input.py input.json

Or create input.json with your story data.
"""

import asyncio
import json
import sys
import os
from agents.orchestrator_agent import QASentinelOrchestrator
from memory.qa_style_memory import QAStyleMemory
from memory.session_store import SessionStore


async def run_from_file(input_file: str):
    """Run pipeline from JSON input file."""
    # Load input
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    session_id = data.get("session_id", "session-1")
    title = data.get("title", "")
    description = data.get("description", "")
    acceptance_criteria = data.get("acceptance_criteria", [])
    qa_context = data.get("qa_context", "")
    
    # Initialize
    memory = QAStyleMemory()
    session_store = SessionStore()
    orchestrator = QASentinelOrchestrator(memory, session_store)
    
    # Run pipeline
    print("Running QA Sentinel pipeline...")
    print(f"Session ID: {session_id}")
    print(f"Title: {title}\n")
    
    result = await orchestrator.run_pipeline(
        session_id=session_id,
        title=title,
        description=description,
        acceptance_criteria=acceptance_criteria,
        qa_context=qa_context
    )
    
    # Output
    print("\n" + "=" * 80)
    print("Pipeline Results:")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "input_story.json"
        # Create example file if it doesn't exist
        if not os.path.exists(input_file):
            example = {
                "session_id": "session-1",
                "title": "User updates profile information",
                "description": "As a user, I want to update my profile so that I can keep my information current and accurate.",
                "acceptance_criteria": [
                    "User can update their name",
                    "User can update their email",
                    "User receives validation error for invalid email format"
                ],
                "qa_context": "Focus on negative testing, usability, and boundary behavior."
            }
            with open(input_file, 'w') as f:
                json.dump(example, f, indent=2)
            print(f"Created example input file: {input_file}")
            print("Edit it with your story data and run again.")
            sys.exit(0)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    asyncio.run(run_from_file(input_file))


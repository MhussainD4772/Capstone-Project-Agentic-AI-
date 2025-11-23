"""Main entry point for QA Sentinel.

This is a demo entrypoint for local testing and development.
This is NOT the production deployment entry for Cloud Run.
"""

import asyncio
import json
from agents.orchestrator_agent import QASentinelOrchestrator
from memory.qa_style_memory import QAStyleMemory
from memory.session_store import SessionStore


async def run_demo():
    """
    Run a complete QA pipeline demo with sample user story.
    
    This function demonstrates the full pipeline:
    1. Initializes memory and session store
    2. Creates orchestrator
    3. Runs pipeline with sample story
    4. Displays results
    """
    # Initialize core components
    memory = QAStyleMemory()
    session_store = SessionStore()
    orchestrator = QASentinelOrchestrator(memory, session_store)
    
    # Sample user story input
    session_id = "session-demo-1"
    title = "User updates profile information"
    description = "As a user, I want to update my profile so that I can keep my information current and accurate."
    acceptance_criteria = [
        "User can update their name",
        "User can update their email",
        "User receives validation error for invalid email format"
    ]
    qa_context = "Focus on negative testing, usability, and boundary behavior."
    
    # Run the complete pipeline
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
    
    # Pretty-print the result
    print("\n" + "=" * 80)
    print("Pipeline Results:")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())


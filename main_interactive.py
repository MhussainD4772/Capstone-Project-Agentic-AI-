"""Interactive entry point for QA Sentinel.

This version allows users to input their own user stories via command-line prompts.
"""

import asyncio
import json
from agents.orchestrator_agent import QASentinelOrchestrator
from memory.qa_style_memory import QAStyleMemory
from memory.session_store import SessionStore


def get_user_input():
    """Prompt user for story input."""
    print("=" * 80)
    print("🛡️  QA Sentinel - Interactive Mode")
    print("=" * 80)
    print()
    
    # Get story title
    title = input("📝 Enter User Story Title: ").strip()
    if not title:
        title = "User updates profile information"
        print(f"   Using default: {title}")
    
    # Get description
    print()
    print("📄 Enter User Story Description (press Enter twice to finish):")
    description_lines = []
    while True:
        line = input()
        if line == "" and description_lines and description_lines[-1] == "":
            break
        description_lines.append(line)
    description = "\n".join(description_lines).strip()
    if not description:
        description = "As a user, I want to update my profile so that I can keep my information current and accurate."
        print(f"   Using default: {description}")
    
    # Get acceptance criteria
    print()
    print("✅ Enter Acceptance Criteria (one per line, press Enter twice to finish):")
    acceptance_criteria = []
    while True:
        ac = input()
        if ac == "" and acceptance_criteria:
            break
        if ac.strip():
            acceptance_criteria.append(ac.strip())
    
    if not acceptance_criteria:
        acceptance_criteria = [
            "User can update their name",
            "User can update their email",
            "User receives validation error for invalid email format"
        ]
        print(f"   Using default acceptance criteria")
    
    # Get QA context
    print()
    qa_context = input("🎯 Enter QA Context (testing focus, style preferences, etc.): ").strip()
    if not qa_context:
        qa_context = "Focus on negative testing, usability, and boundary behavior."
        print(f"   Using default: {qa_context}")
    
    # Get session ID
    print()
    session_id = input("🆔 Enter Session ID (or press Enter for auto-generated): ").strip()
    if not session_id:
        import uuid
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        print(f"   Generated: {session_id}")
    
    return session_id, title, description, acceptance_criteria, qa_context


async def run_pipeline_interactive():
    """Run pipeline with user-provided input."""
    # Get user input
    session_id, title, description, acceptance_criteria, qa_context = get_user_input()
    
    # Initialize core components
    print()
    print("=" * 80)
    print("🚀 Initializing QA Sentinel Pipeline...")
    print("=" * 80)
    memory = QAStyleMemory()
    session_store = SessionStore()
    orchestrator = QASentinelOrchestrator(memory, session_store)
    
    # Display input summary
    print()
    print("📋 Input Summary:")
    print(f"   Session ID: {session_id}")
    print(f"   Title: {title}")
    print(f"   Description: {description[:100]}..." if len(description) > 100 else f"   Description: {description}")
    print(f"   Acceptance Criteria: {len(acceptance_criteria)} items")
    print(f"   QA Context: {qa_context}")
    print()
    
    # Run the complete pipeline
    print("=" * 80)
    print("🔄 Running Pipeline...")
    print("=" * 80)
    print()
    
    try:
        result = await orchestrator.run_pipeline(
            session_id=session_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            qa_context=qa_context
        )
        
        # Pretty-print the result
        print()
        print("=" * 80)
        print("✅ Pipeline Results:")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        print("=" * 80)
        print()
        
        # Summary
        print("📊 Summary:")
        planner = result.get("planner_output", {})
        testcase = result.get("testcase_output", {})
        validation = result.get("global_validation_output", {})
        
        print(f"   ✅ Features: {len(planner.get('features', []))}")
        print(f"   ✅ Scenarios: {len(planner.get('scenarios', []))}")
        print(f"   ✅ Test Cases: {len(testcase.get('test_cases', []))}")
        print(f"   ✅ Edge Cases: {len(testcase.get('edge_cases', []))}")
        print(f"   ✅ Bug Risks: {len(testcase.get('bug_risks', []))}")
        print(f"   ✅ Validation: {'VALID' if validation.get('valid') else 'INVALID'}")
        if validation.get('errors'):
            print(f"   ⚠️  Errors: {len(validation.get('errors', []))}")
        if validation.get('warnings'):
            print(f"   ⚠️  Warnings: {len(validation.get('warnings', []))}")
        
        print()
        print("=" * 80)
        print("✨ Pipeline execution completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Pipeline execution failed:")
        print("=" * 80)
        print(f"Error: {e}")
        print("=" * 80)
        raise


if __name__ == "__main__":
    asyncio.run(run_pipeline_interactive())


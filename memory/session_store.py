"""Session store module.

This module provides a simple in-memory session store for tracking per-story/per-run
state across the QA Sentinel pipeline (planner, testcases, automation, validation).
The implementation uses a simple in-memory dictionary, but the interface is designed
to be easily swappable with a persistent store (e.g., database) in the future
without changing the orchestrator agent code that uses this class.
"""

from typing import Dict, Optional, List
from datetime import datetime


class SessionStore:
    """
    Simple in-memory session store for tracking pipeline state.
    
    This class keeps track of per-story/per-run state across the QA Sentinel pipeline,
    storing outputs from different stages (planner, testcases, automation, validation).
    The orchestrator agent uses this to track state across runs and coordinate
    the multi-agent workflow.
    
    The interface is designed to be easily swappable with a persistent store
    (e.g., database, Redis) in the future without changing the orchestrator agent code.
    
    Attributes:
        _sessions: Dictionary keyed by session_id containing session data
    """
    
    def __init__(self):
        """Initialize an empty SessionStore."""
        self._sessions: Dict[str, Dict] = {}
    
    def start_session(self, session_id: str, title: str, qa_context: str) -> None:
        """
        Start a new session with initial metadata.
        
        Args:
            session_id: Unique identifier for the session
            title: Story title
            qa_context: String describing QA preferences and thought style
        
        Raises:
            ValueError: If session_id already exists
        """
        if session_id in self._sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        self._sessions[session_id] = {
            "metadata": {
                "title": title,
                "created_at": datetime.now(),
                "qa_context": qa_context
            },
            "stages": {
                "planner_output": None,
                "testcase_output": None,
                "automation_output": None,
                "global_validation_output": None
            }
        }
    
    def save_stage_output(self, session_id: str, stage_name: str, data: Dict) -> None:
        """
        Save output from a pipeline stage.
        
        Args:
            session_id: Session identifier
            stage_name: Name of the stage. Must be one of:
                - "planner_output"
                - "testcase_output"
                - "automation_output"
                - "global_validation_output"
            data: Dictionary containing the stage output data
        
        Raises:
            KeyError: If session_id does not exist
            ValueError: If stage_name is invalid
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} does not exist")
        
        valid_stages = [
            "planner_output",
            "testcase_output",
            "automation_output",
            "global_validation_output"
        ]
        
        if stage_name not in valid_stages:
            raise ValueError(
                f"Invalid stage_name: {stage_name}. Must be one of: {valid_stages}"
            )
        
        self._sessions[session_id]["stages"][stage_name] = data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve a session by session_id.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session dictionary if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def list_sessions(self) -> List[str]:
        """
        List all session IDs.
        
        Returns:
            List of all session IDs
        """
        return list(self._sessions.keys())


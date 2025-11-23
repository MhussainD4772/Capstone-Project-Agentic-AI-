"""QA style memory module.

This module provides a simple in-memory memory bank for storing QA examples and preferences.
The implementation uses basic string matching for similarity search, but the interface
is designed to be easily swappable with a vector database (e.g., FAISS) in the future
without changing the agent code that uses this class.
"""

from typing import List, Dict, Any
import re


class QAStyleMemory:
    """
    Simple in-memory memory bank for storing QA examples and preferences.
    
    This class provides long-term memory of how the QA thinks, allowing agents
    to retrieve past examples and preferences. It uses a simple in-memory store
    with basic string matching for similarity search.
    
    The interface is designed to be easily swappable with a vector database
    (e.g., FAISS) in the future without changing the agent code that uses this class.
    The similarity search can be upgraded to semantic similarity using embeddings
    while maintaining the same method signatures.
    
    Attributes:
        _examples: List of stored example dictionaries containing story information
    """
    
    def __init__(self):
        """Initialize an empty QAStyleMemory store."""
        self._examples: List[Dict[str, Any]] = []
    
    def save_example(
        self,
        story_id: str,
        title: str,
        acceptance_criteria: List[str],
        planner_output: Dict[str, Any],
        testcase_output: Dict[str, Any],
        qa_context: str
    ) -> None:
        """
        Save a QA example to memory.
        
        Args:
            story_id: Unique identifier for the story
            title: Story title
            acceptance_criteria: List of acceptance criteria strings
            planner_output: JSON output from StoryPlannerAgent
            testcase_output: JSON output from TestCaseGeneratorAgent
            qa_context: String describing QA preferences and thought style
        """
        example = {
            "story_id": story_id,
            "title": title,
            "acceptance_criteria": acceptance_criteria,
            "planner_output": planner_output,
            "testcase_output": testcase_output,
            "qa_context": qa_context
        }
        self._examples.append(example)
    
    def get_similar_examples(self, query_title: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve similar examples based on title similarity.
        
        Uses simple case-insensitive substring and keyword matching.
        Sorts results by word overlap count and returns top_k matches.
        
        Args:
            query_title: Title to search for similar examples
            top_k: Maximum number of similar examples to return (default: 3)
        
        Returns:
            List of example dictionaries sorted by similarity (most similar first)
        """
        if not self._examples:
            return []
        
        # Normalize query title: lowercase and extract words
        query_lower = query_title.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        # Calculate similarity scores
        scored_examples = []
        for example in self._examples:
            title_lower = example["title"].lower()
            title_words = set(re.findall(r'\w+', title_lower))
            
            # Calculate word overlap
            overlap = len(query_words & title_words)
            
            # Check for substring match (bonus score)
            substring_bonus = 1 if query_lower in title_lower or title_lower in query_lower else 0
            
            # Total score: overlap count + substring bonus
            score = overlap + substring_bonus
            
            if score > 0:
                scored_examples.append((score, example))
        
        # Sort by score (descending) and return top_k
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [example for _, example in scored_examples[:top_k]]
    
    def get_all_examples(self) -> List[Dict[str, Any]]:
        """
        Retrieve all stored examples.
        
        Returns:
            List of all example dictionaries
        """
        return self._examples.copy()
    
    def __len__(self) -> int:
        """
        Return the number of stored examples.
        
        Useful for debugging and orchestration.
        
        Returns:
            Number of examples in memory
        """
        return len(self._examples)
    
    def clear(self) -> None:
        """
        Clear all stored examples from memory.
        
        Useful for resetting memory between evaluation runs.
        """
        self._examples.clear()


# Example usage:
#
# # Initialize memory
# memory = QAStyleMemory()
#
# # Save an example
# memory.save_example(
#     story_id="STORY-001",
#     title="User Login Feature",
#     acceptance_criteria=[
#         "User can log in with valid credentials",
#         "User receives error for invalid credentials"
#     ],
#     planner_output={
#         "features": ["Authentication"],
#         "scenarios": [{"scenario_id": "SC-1", "title": "Valid login"}],
#         "notes": []
#     },
#     testcase_output={
#         "test_cases": [{"id": "TC-1", "title": "Test valid login"}],
#         "edge_cases": [],
#         "bug_risks": []
#     },
#     qa_context="Focus on security and negative testing"
# )
#
# # Retrieve similar examples
# similar = memory.get_similar_examples("Login", top_k=2)
# print(f"Found {len(similar)} similar examples")
#
# # Get all examples
# all_examples = memory.get_all_examples()
# print(f"Total examples: {len(all_examples)}")


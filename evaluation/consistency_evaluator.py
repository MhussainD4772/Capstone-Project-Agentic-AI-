"""Consistency evaluator module.

This module provides a lightweight evaluator that analyzes the consistency
between planner_output and testcase_output. It returns a JSON score and
issues list for use by the orchestrator for optional evaluation.

This is NOT an ADK agent - it is a plain Python class used for evaluation.
"""

from typing import Dict, List, Any, Set


class ConsistencyEvaluator:
    """
    Evaluator that analyzes consistency between planner and test case outputs.
    
    This class performs lightweight consistency checks between StoryPlannerAgent
    output and TestCaseGeneratorAgent output. It evaluates:
    - Coverage: Every scenario has corresponding test cases
    - Consistency: Test cases reference their source scenarios
    - Quality: Test cases have proper structure (Given/When/Then)
    - Alignment: Features and scenarios are properly mapped
    
    Returns a JSON score (0-100) and a list of issues found.
    """
    
    def evaluate(self, planner_output: Dict[str, Any], testcase_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate consistency between planner_output and testcase_output.
        
        Args:
            planner_output: JSON output from StoryPlannerAgent containing:
                - features: list of feature strings
                - scenarios: list of scenario dicts with scenario_id, title, etc.
                - notes: list of notes
                - acceptance_criteria_input: list of acceptance criteria
            testcase_output: JSON output from TestCaseGeneratorAgent containing:
                - test_cases: list of test case dicts with id, title, steps, etc.
                - edge_cases: list of edge case dicts
                - bug_risks: list of bug risk dicts
                - planner_output: original planner output (for reference)
        
        Returns:
            Dictionary with:
            - score: float (0-100) representing consistency score
            - issues: list of issue strings describing problems found
            - coverage: dict with coverage metrics
        """
        issues: List[str] = []
        score_deductions = 0
        max_score = 100
        
        # Extract data structures
        planner_scenarios = planner_output.get("scenarios", [])
        test_cases = testcase_output.get("test_cases", [])
        planner_features = planner_output.get("features", [])
        
        # Get scenario IDs from planner
        scenario_ids = {scenario.get("scenario_id") for scenario in planner_scenarios if scenario.get("scenario_id")}
        
        # Coverage check: Every scenario should have at least one test case
        scenario_coverage = self._check_scenario_coverage(scenario_ids, test_cases, issues)
        if not scenario_coverage["all_covered"]:
            score_deductions += 20
            issues.append(f"Missing test cases for scenarios: {', '.join(scenario_coverage['missing'])}")
        
        # Test case quality check
        quality_issues = self._check_test_case_quality(test_cases, issues)
        score_deductions += quality_issues * 5  # 5 points per quality issue
        
        # Consistency check: Test cases should reference their scenarios
        consistency_issues = self._check_consistency(scenario_ids, test_cases, issues)
        score_deductions += consistency_issues * 3  # 3 points per consistency issue
        
        # Structure validation
        structure_issues = self._check_structure(planner_output, testcase_output, issues)
        score_deductions += structure_issues * 10  # 10 points per structure issue
        
        # Calculate final score
        final_score = max(0, max_score - score_deductions)
        
        # Coverage metrics
        coverage = {
            "total_scenarios": len(scenario_ids),
            "covered_scenarios": len(scenario_ids) - len(scenario_coverage.get("missing", [])),
            "total_test_cases": len(test_cases),
            "coverage_percentage": (
                (len(scenario_ids) - len(scenario_coverage.get("missing", []))) / len(scenario_ids) * 100
                if scenario_ids else 100
            )
        }
        
        return {
            "score": round(final_score, 2),
            "issues": issues,
            "coverage": coverage
        }
    
    def _check_scenario_coverage(
        self, scenario_ids: Set[str], test_cases: List[Dict[str, Any]], issues: List[str]
    ) -> Dict[str, Any]:
        """Check if all scenarios have corresponding test cases."""
        covered_scenarios = set()
        
        for test_case in test_cases:
            title = test_case.get("title", "").lower()
            steps = " ".join(test_case.get("steps", [])).lower()
            combined_text = f"{title} {steps}"
            
            # Check if any scenario_id is mentioned in test case
            for scenario_id in scenario_ids:
                if scenario_id.lower() in combined_text or f"scenario {scenario_id.lower()}" in combined_text:
                    covered_scenarios.add(scenario_id)
        
        missing = scenario_ids - covered_scenarios
        
        return {
            "all_covered": len(missing) == 0,
            "missing": list(missing),
            "covered": list(covered_scenarios)
        }
    
    def _check_test_case_quality(self, test_cases: List[Dict[str, Any]], issues: List[str]) -> int:
        """Check quality of test cases (Given/When/Then structure)."""
        quality_issues = 0
        
        for test_case in test_cases:
            test_id = test_case.get("id", "unknown")
            steps = test_case.get("steps", [])
            
            has_given = any(step.strip().lower().startswith("given") for step in steps)
            has_when = any(step.strip().lower().startswith("when") for step in steps)
            has_then = any(step.strip().lower().startswith("then") for step in steps)
            
            if not has_given:
                issues.append(f"Test case {test_id} missing 'Given' step")
                quality_issues += 1
            if not has_when:
                issues.append(f"Test case {test_id} missing 'When' step")
                quality_issues += 1
            if not has_then:
                issues.append(f"Test case {test_id} missing 'Then' step")
                quality_issues += 1
            
            if not test_case.get("expected_result"):
                issues.append(f"Test case {test_id} missing expected_result")
                quality_issues += 1
        
        return quality_issues
    
    def _check_consistency(
        self, scenario_ids: Set[str], test_cases: List[Dict[str, Any]], issues: List[str]
    ) -> int:
        """Check consistency between scenarios and test cases."""
        consistency_issues = 0
        
        # Check if test cases reference scenarios
        for test_case in test_cases:
            test_id = test_case.get("id", "unknown")
            title = test_case.get("title", "").lower()
            steps = " ".join(test_case.get("steps", [])).lower()
            combined_text = f"{title} {steps}"
            
            # Check if test case references any scenario
            references_scenario = any(
                scenario_id.lower() in combined_text or f"scenario {scenario_id.lower()}" in combined_text
                for scenario_id in scenario_ids
            )
            
            if not references_scenario and scenario_ids:
                issues.append(f"Test case {test_id} does not reference any scenario")
                consistency_issues += 1
        
        return consistency_issues
    
    def _check_structure(
        self, planner_output: Dict[str, Any], testcase_output: Dict[str, Any], issues: List[str]
    ) -> int:
        """Check basic structure validity."""
        structure_issues = 0
        
        # Check planner_output structure
        if not planner_output.get("scenarios"):
            issues.append("planner_output missing 'scenarios' field")
            structure_issues += 1
        
        if not planner_output.get("features"):
            issues.append("planner_output missing 'features' field")
            structure_issues += 1
        
        # Check testcase_output structure
        if not testcase_output.get("test_cases"):
            issues.append("testcase_output missing 'test_cases' field")
            structure_issues += 1
        
        return structure_issues


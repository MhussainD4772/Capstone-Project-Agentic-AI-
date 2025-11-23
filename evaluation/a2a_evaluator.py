"""A2A (Agent-to-Agent) evaluator module.

This module implements a lightweight A2A-style evaluator that simulates
agent-to-agent meta-evaluation. It provides scoring and qualitative reasoning
for planner and testcase outputs without actually calling an LLM.

This demonstrates the A2A pattern for the Kaggle rubric while being a
deterministic, rule-based evaluator.
"""

from typing import Dict, List, Any


class A2AEvaluator:
    """
    A2A-style evaluator that simulates agent-to-agent meta-evaluation.
    
    This class simulates an agent evaluating the outputs of other agents,
    providing both quantitative scores and qualitative reasoning. It follows
    the A2A pattern without actually calling an LLM, making it deterministic
    and suitable for evaluation pipelines.
    
    The evaluator assesses:
    - Completeness: Are all scenarios covered?
    - Quality: Are test cases well-structured?
    - Alignment: Do outputs align with requirements?
    - Reasoning: Provides qualitative explanations
    """
    
    def evaluate(self, planner_output: Dict[str, Any], testcase_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate planner and testcase outputs using A2A-style meta-evaluation.
        
        This method simulates an agent evaluating other agents' outputs,
        providing scores and qualitative reasoning.
        
        Args:
            planner_output: JSON output from StoryPlannerAgent containing:
                - features: list of feature strings
                - scenarios: list of scenario dicts with scenario_id, title, etc.
                - notes: list of notes
                - acceptance_criteria_input: list of acceptance criteria
            testcase_output: JSON output from TestCaseGeneratorAgent containing:
                - test_cases: list of test case dicts
                - edge_cases: list of edge case dicts
                - bug_risks: list of bug risk dicts
                - planner_output: original planner output
        
        Returns:
            Dictionary with:
            - overall_score: float (0-100) overall evaluation score
            - component_scores: dict with individual component scores
            - qualitative_reasoning: list of qualitative assessment strings
            - quantitative_metrics: dict with numerical metrics
            - recommendations: list of improvement recommendations
        """
        # Extract data
        planner_scenarios = planner_output.get("scenarios", [])
        test_cases = testcase_output.get("test_cases", [])
        edge_cases = testcase_output.get("edge_cases", [])
        bug_risks = testcase_output.get("bug_risks", [])
        planner_features = planner_output.get("features", [])
        
        # Initialize results
        qualitative_reasoning: List[str] = []
        component_scores: Dict[str, float] = {}
        quantitative_metrics: Dict[str, Any] = {}
        recommendations: List[str] = []
        
        # 1. Completeness Evaluation
        completeness_score, completeness_reasoning, completeness_metrics = self._evaluate_completeness(
            planner_scenarios, test_cases
        )
        component_scores["completeness"] = completeness_score
        qualitative_reasoning.extend(completeness_reasoning)
        quantitative_metrics.update(completeness_metrics)
        
        # 2. Quality Evaluation
        quality_score, quality_reasoning, quality_metrics = self._evaluate_quality(test_cases)
        component_scores["quality"] = quality_score
        qualitative_reasoning.extend(quality_reasoning)
        quantitative_metrics.update(quality_metrics)
        
        # 3. Alignment Evaluation
        alignment_score, alignment_reasoning, alignment_metrics = self._evaluate_alignment(
            planner_output, testcase_output
        )
        component_scores["alignment"] = alignment_score
        qualitative_reasoning.extend(alignment_reasoning)
        quantitative_metrics.update(alignment_metrics)
        
        # 4. Edge Case & Risk Coverage
        coverage_score, coverage_reasoning, coverage_metrics = self._evaluate_coverage(
            edge_cases, bug_risks, planner_scenarios
        )
        component_scores["coverage"] = coverage_score
        qualitative_reasoning.extend(coverage_reasoning)
        quantitative_metrics.update(coverage_metrics)
        
        # Calculate overall score (weighted average)
        overall_score = (
            completeness_score * 0.30 +
            quality_score * 0.30 +
            alignment_score * 0.25 +
            coverage_score * 0.15
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            component_scores, quantitative_metrics, qualitative_reasoning
        )
        
        return {
            "overall_score": round(overall_score, 2),
            "component_scores": component_scores,
            "qualitative_reasoning": qualitative_reasoning,
            "quantitative_metrics": quantitative_metrics,
            "recommendations": recommendations
        }
    
    def _evaluate_completeness(
        self, scenarios: List[Dict[str, Any]], test_cases: List[Dict[str, Any]]
    ) -> tuple[float, List[str], Dict[str, Any]]:
        """Evaluate completeness: Are all scenarios covered by test cases?"""
        reasoning: List[str] = []
        metrics: Dict[str, Any] = {}
        
        scenario_ids = {s.get("scenario_id") for s in scenarios if s.get("scenario_id")}
        covered_scenarios = set()
        
        for test_case in test_cases:
            title = test_case.get("title", "").lower()
            steps = " ".join(test_case.get("steps", [])).lower()
            combined = f"{title} {steps}"
            
            for scenario_id in scenario_ids:
                if scenario_id and scenario_id.lower() in combined:
                    covered_scenarios.add(scenario_id)
        
        coverage_ratio = len(covered_scenarios) / len(scenario_ids) if scenario_ids else 1.0
        score = coverage_ratio * 100
        
        metrics["total_scenarios"] = len(scenario_ids)
        metrics["covered_scenarios"] = len(covered_scenarios)
        metrics["coverage_ratio"] = round(coverage_ratio, 3)
        
        if coverage_ratio == 1.0:
            reasoning.append("All scenarios are covered by test cases. Excellent completeness.")
        elif coverage_ratio >= 0.8:
            missing = scenario_ids - covered_scenarios
            reasoning.append(
                f"Good coverage ({coverage_ratio:.1%}), but {len(missing)} scenario(s) lack test cases: {', '.join(missing)}"
            )
        else:
            missing = scenario_ids - covered_scenarios
            reasoning.append(
                f"Low coverage ({coverage_ratio:.1%}). Missing test cases for {len(missing)} scenario(s): {', '.join(missing)}"
            )
        
        return score, reasoning, metrics
    
    def _evaluate_quality(self, test_cases: List[Dict[str, Any]]) -> tuple[float, List[str], Dict[str, Any]]:
        """Evaluate quality: Are test cases well-structured?"""
        reasoning: List[str] = []
        metrics: Dict[str, Any] = {}
        
        if not test_cases:
            return 0.0, ["No test cases found."], {"total_test_cases": 0}
        
        total = len(test_cases)
        well_structured = 0
        has_given_when_then = 0
        has_expected_result = 0
        
        for test_case in test_cases:
            steps = test_case.get("steps", [])
            has_given = any(s.strip().lower().startswith("given") for s in steps)
            has_when = any(s.strip().lower().startswith("when") for s in steps)
            has_then = any(s.strip().lower().startswith("then") for s in steps)
            has_expected = bool(test_case.get("expected_result"))
            
            if has_given and has_when and has_then:
                has_given_when_then += 1
            if has_expected:
                has_expected_result += 1
            if has_given and has_when and has_then and has_expected:
                well_structured += 1
        
        gwt_ratio = has_given_when_then / total
        expected_ratio = has_expected_result / total
        structured_ratio = well_structured / total
        
        score = (gwt_ratio * 0.5 + expected_ratio * 0.3 + structured_ratio * 0.2) * 100
        
        metrics["total_test_cases"] = total
        metrics["with_given_when_then"] = has_given_when_then
        metrics["with_expected_result"] = has_expected_result
        metrics["well_structured"] = well_structured
        
        if structured_ratio >= 0.9:
            reasoning.append(f"Excellent test case quality: {well_structured}/{total} are well-structured with Given/When/Then and expected results.")
        elif structured_ratio >= 0.7:
            reasoning.append(f"Good test case quality: {well_structured}/{total} are well-structured. Some test cases lack proper structure.")
        else:
            reasoning.append(f"Test case quality needs improvement: Only {well_structured}/{total} are well-structured. Many lack Given/When/Then steps or expected results.")
        
        return score, reasoning, metrics
    
    def _evaluate_alignment(
        self, planner_output: Dict[str, Any], testcase_output: Dict[str, Any]
    ) -> tuple[float, List[str], Dict[str, Any]]:
        """Evaluate alignment: Do outputs align with requirements?"""
        reasoning: List[str] = []
        metrics: Dict[str, Any] = {}
        
        planner_features = planner_output.get("features", [])
        planner_scenarios = planner_output.get("scenarios", [])
        test_cases = testcase_output.get("test_cases", [])
        
        # Check if test cases align with planner features
        feature_alignment = len(planner_features) > 0 and len(test_cases) > 0
        scenario_alignment = len(planner_scenarios) > 0 and len(test_cases) > 0
        
        alignment_score = 100.0 if (feature_alignment and scenario_alignment) else 50.0
        
        metrics["planner_features"] = len(planner_features)
        metrics["planner_scenarios"] = len(planner_scenarios)
        metrics["test_cases"] = len(test_cases)
        metrics["feature_alignment"] = feature_alignment
        metrics["scenario_alignment"] = scenario_alignment
        
        if feature_alignment and scenario_alignment:
            reasoning.append("Outputs are well-aligned: Test cases correspond to planner features and scenarios.")
        else:
            reasoning.append("Alignment issues detected: Some planner outputs lack corresponding test cases.")
        
        return alignment_score, reasoning, metrics
    
    def _evaluate_coverage(
        self, edge_cases: List[Dict[str, Any]], bug_risks: List[Dict[str, Any]], scenarios: List[Dict[str, Any]]
    ) -> tuple[float, List[str], Dict[str, Any]]:
        """Evaluate edge case and bug risk coverage."""
        reasoning: List[str] = []
        metrics: Dict[str, Any] = {}
        
        edge_case_count = len(edge_cases)
        bug_risk_count = len(bug_risks)
        scenario_count = len(scenarios)
        
        # Score based on having edge cases and bug risks
        edge_score = min(edge_case_count * 10, 50)  # Max 50 points
        risk_score = min(bug_risk_count * 10, 50)  # Max 50 points
        
        total_score = edge_score + risk_score
        
        metrics["edge_cases"] = edge_case_count
        metrics["bug_risks"] = bug_risk_count
        metrics["scenarios"] = scenario_count
        
        if edge_case_count > 0 and bug_risk_count > 0:
            reasoning.append(
                f"Good coverage: {edge_case_count} edge case(s) and {bug_risk_count} bug risk(s) identified. "
                "This shows thorough testing consideration."
            )
        elif edge_case_count > 0:
            reasoning.append(
                f"Edge cases identified ({edge_case_count}), but no bug risks documented. "
                "Consider adding bug risk analysis."
            )
        elif bug_risk_count > 0:
            reasoning.append(
                f"Bug risks identified ({bug_risk_count}), but no edge cases documented. "
                "Consider adding edge case scenarios."
            )
        else:
            reasoning.append(
                "No edge cases or bug risks identified. Consider adding edge case scenarios "
                "and bug risk analysis for more comprehensive testing."
            )
        
        return total_score, reasoning, metrics
    
    def _generate_recommendations(
        self, component_scores: Dict[str, float], metrics: Dict[str, Any], reasoning: List[str]
    ) -> List[str]:
        """Generate improvement recommendations based on evaluation."""
        recommendations: List[str] = []
        
        # Completeness recommendations
        if component_scores.get("completeness", 100) < 80:
            recommendations.append(
                "Improve scenario coverage: Ensure every scenario from the planner has at least one corresponding test case."
            )
        
        # Quality recommendations
        if component_scores.get("quality", 100) < 80:
            recommendations.append(
                "Enhance test case structure: Ensure all test cases include Given/When/Then steps and expected results."
            )
        
        # Coverage recommendations
        if metrics.get("edge_cases", 0) == 0:
            recommendations.append("Add edge case scenarios to improve test coverage.")
        
        if metrics.get("bug_risks", 0) == 0:
            recommendations.append("Document bug risks to help identify potential issues.")
        
        # Overall recommendations
        overall = sum(component_scores.values()) / len(component_scores) if component_scores else 0
        if overall < 70:
            recommendations.append(
                "Overall quality needs improvement. Review planner output and test case generation for better alignment."
            )
        
        return recommendations


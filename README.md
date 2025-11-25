# 🧠 QA Sentinel – Multi-Agent Test Case Generation System  
Google × Kaggle — Agentic AI Intensive (Capstone Project)

QA Sentinel is a fully automated, production-style **multi-agent QA pipeline** powered by **Google’s Agent Development Kit (ADK)** and **Gemini models**.  

It converts a user story into a complete QA package:  
Features → Scenarios → Test Cases → Edge Cases → Bug Risks → Validation.

---
## 📌 Problem Statement

Manually generating QA assets is slow, inconsistent, and error-prone.  
QA teams must:
- Interpret vague user stories  
- Break them into features & scenarios  
- Ensure acceptance criteria coverage  
- Write structured Given/When/Then test cases  
- Perform quality checks across multiple outputs  

This process is repetitive and leads to:
- Coverage gaps  
- Inconsistent structure  
- Validation overhead  
- Slower QA cycles  

We needed a system that automates this entire workflow with consistency and quality.

---

## 🚀 Solution Overview

**QA Sentinel** automates end-to-end QA planning using a coordinated set of AI agents.

The system performs:

### ✔ Story Analysis & Decomposition  
Breaks user stories into features, scenarios, insights.

### ✔ Automated Test Case Generation  
Produces structured test cases with GWT steps, preconditions, and expected results.

### ✔ Edge Case & Bug Risk Discovery  
Expands test coverage intelligently.

### ✔ Multi-Agent Validation  
Ensures correctness of scenarios, structure, coverage, and alignment.

### ✔ Memory-Augmented Reasoning  
Uses FAISS vector memory to improve future outputs.

### ✔ Deterministic Evaluation  
Consistency scoring + A2A (Agent-to-Agent) meta-evaluation.

### ✔ MCP Output Tools  
Exports results as JSON/Markdown for real QA workflow usage.

This creates a **robust, repeatable, high-coverage QA generation pipeline**.

---

## 🧩 System Architecture

### High-Level System Architecture

```mermaid
    "Input"
        [User Story<br/>Title, Description, AC, QA Context]
    
    "Orchestrator Layer"
        [QASentinelOrchestrator<br/>Session Management & Coordination]
    
    "Agent Layer"
        [Story Planner Loop<br/>ADK v1 Loop]
        [Test Case Generator Loop<br/>ADK v1 Loop]
        [Global Validator Loop<br/>ADK v1 Loop]
    
    "Memory Layer"
        [QAStyleMemory<br/>FAISS Vector DB]
        [SessionStore<br/>In-Memory State]
    
    "Evaluation Layer"
        [ConsistencyEvaluator<br/>Rule-based]
        [A2AEvaluator<br/>Meta-evaluation]
    
    "Export Layer"
        [MCP Export Server<br/>Markdown & JSON]
    
    "Output"
        [Structured JSON<br/>Test Cases, Edge Cases,<br/>Bug Risks, Validation]

```

---

## 🛠️ Agents Breakdown

### 1. Story Planner (LoopAgent)
Breaks the story into:
- Features (3–8 items)
- Structured scenarios (SC-1, SC-2…)
- AC mapping
- Notes & insights

Validation ensures:
- Non‑empty features
- Every AC has ≥1 scenario
- Strict JSON formatting

---

### 2. Test Case Generator (LoopAgent)
Generates:
- 1–3 test cases per scenario  
- Preconditions  
- Gherkin Given/When/Then steps  
- Expected results  
- Edge cases  
- Bug risks  

Validation ensures:
- All scenarios referenced
- G/W/T structure exists
- Expected result exists

---

### 3. Global Validator Agent
Checks:
- Coverage completeness  
- Step quality  
- Logical flow  
- Missing scenarios/tests  
- JSON structure  

---

## 🧠 Memory Layer (FAISS)
Stores:
- Title  
- AC  
- Planner output  
- Test case output  

Used for:
- Similar test case pattern retrieval  
- Style consistency  

---

## 📝 Evaluation Layer
### ✔ ConsistencyEvaluator
Rule-based scoring of:
- Scenario coverage  
- GWT structure  
- Scenario reference  
- Output structure  

### ✔ A2AEvaluator  
Simulates agent-to-agent evaluation:
- Component scores  
- Reasoning  
- Recommendations  
- Metrics  

---

## 🧰 Tools & Utilities

### MCP File Export Tool
- Saves JSON  
- Saves Markdown  

### Logging Layer
- Rotating logs  
- Structured timestamps  

### Tracing Module
- Tracks duration of each stage  

### SessionStore
- Tracks planner/testcase/validator outputs  

### JSON Extractor
- Robust ADK event parsing  

---

## 📂 Project Structure

```
qa-sentinel/
│
├── agents/
│   ├── story_planner_agent.py
│   ├── testcase_generator_agent.py
│   ├── global_validator_agent.py
│   ├── orchestrator_agent.py
│   └── adk_v1_compat.py
│
├── memory/
│   ├── qa_style_memory.py
│   └── session_store.py
│
├── evaluation/
│   ├── consistency_evaluator.py
│   └── a2a_evaluator.py
│
├── tools/
│   └── file_export_mcp.py
│
├── observability/
│   ├── logging_config.py
│   └── tracing.py
│
├── config/
│   ├── model_config.py
│   └── settings.py
│
├── examples/
│   ├── sample_input_story.md
│   └── sample_output_tests.md
│
├── deployment/
│   ├── Dockerfile
│   ├── cloudrun_deploy.md
│   └── agent_engine_setup.md
│
├── exports/
├── main.py
├── requirements.txt
├── .env
├── LICENSE
└── README.md
```

## 🧪 How to Run Locally

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Add Your Gemini API Key

Create `.env`:

```env
GOOGLE_API_KEY=your_key_here
```

### 4. Run Pipeline

```bash
python main_interactive.py
```

**What happens next:**
- `It will ask for User story title, Description, Acceptance Criteria and QA context.`
- `Then the pipeline will run and you will get the complete output.`

**Outputs will be saved in:**
- `exports/markdown/`
- `exports/json/`

---

## 🔍 Example Output (Summary)

- **Planner generates**: SC-1 ... SC-n scenarios
- **Generator produces**: TC-1 ... TC-n test cases
- **Validator returns**: `{"valid": true, "errors": []}`
- **Evaluators produce**: Scores 0–100
- **Markdown files**: Saved automatically

### Sample Planner Output

```json
{
  "features": ["Profile Update - Name", "Profile Update - Email"],
  "scenarios": [
    {
      "scenario_id": "SC-1",
      "title": "Update Name Successfully",
      "acceptance_criteria": "User can update their name",
      "tags": ["positive", "name"]
    }
  ],
  "notes": ["Consider localization for name field"],
  "acceptance_criteria_input": ["User can update their name", ...]
}
```

### Sample Test Case Output

```json
{
  "test_cases": [
    {
      "id": "TC-1",
      "title": "Verify Successful Name Update - SC-1",
      "preconditions": ["User is logged in"],
      "steps": [
        "Given the user is on the profile page",
        "When the user updates their first name to 'John'",
        "Then the profile page should display 'John' as the updated name"
      ],
      "expected_result": "User's name is successfully updated and displayed."
    }
  ],
  "edge_cases": [{"id": "EC-1", "description": "Test with extremely long names"}],
  "bug_risks": [{"id": "BR-1", "description": "XSS vulnerability in name fields"}]
}
```

---

## ⭐ Why This Matters (Value Statement)

**QA Sentinel reduces:**
- ⏱️ 6–10 hours of QA planning per sprint
- 🔄 Manual duplication across acceptance criteria
- ❌ Gap-failures between scenarios & test cases

**And increases:**
- ✅ Consistency
- ✅ Coverage
- ✅ Edge-case discovery
- ✅ QA productivity

It represents the future of agentic QA automation.

---

## 🔗 Project Links

**GitHub Repo**: https://github.com/MhussainD4772/Capstone-Project-Agentic-AI-

---

## 📄 License

MIT License — see LICENSE file.

---

<div align="center">

**Built with Google ADK v1, Gemini 2.0 Flash, and Python**

⭐ **Star this repo if you find it useful!** ⭐

</div>

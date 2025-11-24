# 📖 QA Sentinel - Usage Guide

## How to Run with Your Own Input

You have **3 ways** to run QA Sentinel with your own user stories:

---

## Option 1: Interactive Mode (Recommended) 🎯

**Best for**: Trying different stories quickly

```bash
cd "/Users/chummu/Projects/Capstone Project (Agentic AI)/qa-sentinel"
source venv/bin/activate
python main_interactive.py
```

**What happens:**
- Prompts you to enter:
  - Story Title
  - Description
  - Acceptance Criteria (one per line)
  - QA Context
  - Session ID (optional)
- Runs the pipeline
- Shows complete results

**Example session:**
```
📝 Enter User Story Title: User login functionality
📄 Enter User Story Description: As a user, I want to login...
✅ Enter Acceptance Criteria:
   User can login with valid credentials
   User sees error for invalid credentials
   (press Enter twice to finish)
🎯 Enter QA Context: Focus on security testing
```

---

## Option 2: JSON File Input 📄

**Best for**: Reusing the same story or batch processing

### Step 1: Edit `input_story.json`

```json
{
  "session_id": "my-session-1",
  "title": "Your story title here",
  "description": "Your story description here",
  "acceptance_criteria": [
    "AC 1",
    "AC 2",
    "AC 3"
  ],
  "qa_context": "Your QA testing focus"
}
```

### Step 2: Run

```bash
cd "/Users/chummu/Projects/Capstone Project (Agentic AI)/qa-sentinel"
source venv/bin/activate
python run_with_input.py input_story.json
```

---

## Option 3: Edit main.py Directly ✏️

**Best for**: Quick testing with hardcoded data

Edit `main.py` lines 30-38:

```python
title = "Your story title"
description = "Your story description"
acceptance_criteria = [
    "Your AC 1",
    "Your AC 2"
]
qa_context = "Your QA context"
```

Then run:
```bash
python main.py
```

---

## 📸 What You'll Get

All methods produce the same output:

1. **Story Planner Output**
   - Features list
   - Scenarios (SC-1, SC-2, ...)
   - Notes and insights

2. **Test Case Generator Output**
   - Test cases (TC-1, TC-2, ...) with Given/When/Then steps
   - Edge cases (EC-1, EC-2, ...)
   - Bug risks (BR-1, BR-2, ...)

3. **Global Validator Output**
   - Validation status (valid: true/false)
   - Errors and warnings

---

## 💡 Quick Start

**Easiest way to try it:**

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run interactive mode
python main_interactive.py

# 3. Follow the prompts!
```

---

## 🎬 Example Workflow

1. Run `python main_interactive.py`
2. Enter your user story details when prompted
3. Wait 30-60 seconds for processing
4. See complete test cases, edge cases, and validation
5. Take screenshots of the output!

---

**That's it!** You can now input any user story and get test cases! 🚀


# Schmekla Agent Workflow Documentation

## Overview

This document defines the multi-agent orchestration workflow for Schmekla development. The key principle is **MINIMAL CONTEXT for Main Claude** - it only invokes agents and receives summaries, never reading code directly.

---

## Core Principle: Minimal Context Coordinator

**Main Claude (Coordinator) should:**
- Invoke agents via Task tool
- Receive structured summaries
- Report results to user

**Main Claude should NOT:**
- Read code files directly
- Act "as" any agent (no "acting as Orchestrator")
- Make architectural decisions
- Review code quality

---

## Agent Roles

### 1. Main Claude (Coordinator)
**Purpose:** Minimal-context orchestration hub.

**Responsibilities:**
- Receive user requests
- Invoke `schmekla-boss` with the request
- Receive final summary from boss
- Report to user

**Context Usage:** MINIMAL (< 5% of conversation)

---

### 2. schmekla-boss (Orchestrator)
**Purpose:** Full workflow coordination - the central hub that manages everything.

**Responsibilities:**
- Receive request from Main Claude
- Invoke `architect` for design/planning
- Spawn 1-3 `schmekla-coder` agents (parallel)
- Collect coder results
- Invoke `code-reviewer` for quality check
- Handle fix cycles if needed
- Return structured summary to Main Claude

**Agent Count Decision:**
| Condition | Agents |
|-----------|--------|
| 1-2 tasks | 1 |
| 3-5 tasks, different files | 2 |
| 6+ tasks, 3+ file groups | 3 |
| Tasks share files | 1 |

---

### 3. architect
**Purpose:** Design implementation plans and task assignments.

**Responsibilities:**
- Analyze requirements
- Design implementation approach
- Break work into parallelizable tasks
- Assign tasks to code agents (non-overlapping files)
- Define acceptance criteria

**Output Format:**
```json
{
  "implementation_plan": "Brief description",
  "task_assignments": [
    {
      "agent_id": 1,
      "task": "Description",
      "files": ["src/path/file.py"],
      "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    }
  ],
  "agent_count": 1
}
```

---

### 4. schmekla-coder (Code Agent)
**Purpose:** Implement code changes.

**Responsibilities:**
- Read existing code before changes
- Implement assigned task
- Follow existing patterns
- Report completion

**Output Format:**
```
AGENT [N] COMPLETE

Files Modified:
- src/path/file.py (XX lines added)

Changes:
1. Added X feature
2. Modified Y method

Summary: Brief description
```

---

### 5. code-reviewer
**Purpose:** Final quality gate before completion.

**Responsibilities:**
- Review all code changes via git diff
- Check security, quality, patterns
- Return verdict

**Output Format:**
```json
{
  "verdict": "APPROVED | APPROVED_WITH_WARNINGS | CHANGES_REQUESTED",
  "critical_issues": [],
  "warnings": [],
  "can_proceed": true
}
```

---

## Workflow Diagram

```
User Request
     |
     v
+------------------+
|   MAIN CLAUDE    |  (MINIMAL context)
|   - Invoke boss  |
|   - Wait         |
|   - Report       |
+--------+---------+
         |
         | Single Task invocation
         v
+------------------+
|  schmekla-boss   |  (Orchestrator - handles EVERYTHING)
+--------+---------+
         |
         | 1. Invoke architect
         v
+------------------+
|    architect     |  Design & task assignment
+--------+---------+
         |
         | 2. Launch coders (parallel)
         v
+--------+---------+---------+
|        |         |         |
v        v         v         v
+------+ +------+ +------+
|CODER | |CODER | |CODER |  (1-3 parallel)
|  1   | |  2   | |  3   |
+--+---+ +--+---+ +--+---+
   |        |        |
   +--------+--------+
            |
            | 3. Collect results
            v
+------------------+
|  schmekla-boss   |
+--------+---------+
         |
         | 4. Invoke reviewer
         v
+------------------+
|  code-reviewer   |
+--------+---------+
         |
         | 5. Return verdict
         v
+------------------+
|  schmekla-boss   |
+--------+---------+
         |
         | If CHANGES_REQUESTED: loop back to coders
         | If APPROVED: return summary
         v
+------------------+
|   MAIN CLAUDE    |
|   Reports to     |
|   user           |
+------------------+
```

---

## Main Claude Invocation Protocol

### Step 1: User Makes Request
```
User: "Add rubber band selection to viewport"
```

### Step 2: Main Claude Invokes Boss (ONE Task call)
```
Main Claude response:
"I'll delegate this to the schmekla-boss agent to orchestrate the full implementation."

[Invoke Task tool with schmekla-boss]
```

### Step 3: Main Claude Receives Summary
```
Boss returns:
{
  "status": "COMPLETE",
  "files_modified": ["viewport.py", "interaction.py"],
  "code_review": "APPROVED",
  "summary": "Rubber band selection implemented with drag tracking and visual feedback"
}
```

### Step 4: Main Claude Reports to User
```
Main Claude:
"Feature complete!

Summary:
- Rubber band selection implemented
- Files modified: viewport.py, interaction.py
- Code review: APPROVED
- Ready for testing"
```

---

## Boss Invocation Template

When Main Claude invokes schmekla-boss:

```markdown
Orchestrate the implementation of this feature:

**Feature:** [Feature name]
**User Request:** [Original user request]
**Requirements:** [Any specific requirements]

**Your workflow:**
1. Invoke architect to create implementation plan
2. Launch 1-3 schmekla-coder agents based on task count
3. Collect coder results
4. Invoke code-reviewer for quality check
5. If CHANGES_REQUESTED, coordinate fixes and re-review
6. Return final summary to me

**Return format:**
{
  "status": "COMPLETE | IN_PROGRESS | BLOCKED",
  "files_modified": [...],
  "code_review": "APPROVED | CHANGES_REQUESTED",
  "summary": "Brief description"
}
```

---

## Parallel Code Agent Execution

Boss launches coders in a SINGLE message with multiple Task calls:

```xml
<function_calls>
<invoke name="Task">
  <parameter name="description">Coder 1: Core logic</parameter>
  <parameter name="prompt">Implement [task 1]...</parameter>
  <parameter name="subagent_type">schmekla-coder</parameter>
</invoke>
<invoke name="Task">
  <parameter name="description">Coder 2: UI updates</parameter>
  <parameter name="prompt">Implement [task 2]...</parameter>
  <parameter name="subagent_type">schmekla-coder</parameter>
</invoke>
</function_calls>
```

**WRONG:** Sequential launches in separate messages.

---

## Error Handling & Fix Cycles

If code-reviewer returns `CHANGES_REQUESTED`:

1. Boss categorizes issues by responsible coder
2. Boss invokes affected coders with fix instructions
3. Boss runs code-reviewer again
4. Repeat until APPROVED

---

## Key Rules

### 1. Main Claude = Minimal Context
- NEVER read code files
- NEVER act "as" an agent
- ONLY invoke schmekla-boss
- ONLY report summaries

### 2. Boss = Central Orchestrator
- Handles ALL internal coordination
- Invokes architect, coders, reviewer
- Manages fix cycles
- Returns structured summaries

### 3. Parallel Execution
- Launch coders in SINGLE message
- Each coder works on non-overlapping files
- Wait for ALL to complete before review

### 4. Code Review = Mandatory
- EVERY code change reviewed
- No completion without APPROVED verdict

---

## Task Structure (Boss to Coder)

```json
{
  "task_id": "T001",
  "title": "Implement drag tracking",
  "files": [
    {"path": "src/ui/viewport.py", "action": "modify"}
  ],
  "implementation_steps": [
    "Add _drag_start attribute",
    "Track mouse events",
    "Calculate selection rectangle"
  ],
  "acceptance_criteria": [
    "Drag start/end captured",
    "Rectangle coordinates correct",
    "No regression in click selection"
  ],
  "reference_code": ["src/ui/interaction.py:100-150"]
}
```

---

## Code Review Checklist

### CRITICAL (Blocks Approval)
- [ ] No hardcoded credentials
- [ ] No injection vulnerabilities
- [ ] Input validation present

### HIGH (Should Fix)
- [ ] Functions < 50 lines
- [ ] Proper error handling
- [ ] Type hints on public methods

### SCHMEKLA-SPECIFIC
- [ ] Uses Signal-Slot for UI
- [ ] Follows patterns in LEARNED.md
- [ ] Updates actor colors without mesh re-add

---

## Example: Complete Workflow

```
USER: "Add Ctrl+click multi-selection"

MAIN CLAUDE:
"I'll delegate this to schmekla-boss."
[Invokes schmekla-boss]

BOSS (internally):
1. Invokes architect → gets 2-task plan
2. Launches 2 coders in parallel:
   - Coder 1: interaction.py (Ctrl detection)
   - Coder 2: viewport.py (selection toggle)
3. Collects results (both COMPLETE)
4. Invokes code-reviewer → APPROVED
5. Returns summary

MAIN CLAUDE:
"Feature complete!
- Ctrl+click multi-selection implemented
- Files: interaction.py, viewport.py
- Review: APPROVED
- Ready for testing"
```

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-27 | 1.0 | Initial workflow documentation |
| 2026-01-27 | 1.1 | Added Orchestrator agent count logic |
| 2026-01-27 | 2.0 | **Major revision**: Minimal-context coordinator pattern, Boss handles all internal orchestration |

# Schmekla Agent Team Overview

This document describes the agent team structure and their roles.

**Last Updated**: 2026-01-26

---

## Team Hierarchy

```
                    ┌─────────────┐
                    │    USER     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    BOSS     │  ◄── User interface, orchestration
                    │  (Manager)  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │  ARCHITECT  │  │   CODER     │  │ RESEARCHER  │
   │  (Planner)  │  │ (Developer) │  │  (Analyst)  │
   └─────────────┘  └──────┬──────┘  └─────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │   CODE      │  │   BUILD     │  │  REFACTOR   │
   │  REVIEWER   │  │   ERROR     │  │  CLEANER    │
   └─────────────┘  │  RESOLVER   │  └─────────────┘
                    └─────────────┘
```

---

## Core Agents

### 1. Boss (Manager)
**File**: `schmekla-boss.md`
**Role**: User Interface & Orchestration

| Responsibility | Description |
|----------------|-------------|
| User Communication | Receive requests, report results |
| Task Delegation | Assign work to Architect/Coder/Researcher |
| Progress Tracking | Update .md files after completions |
| Validation | Run app, verify features work |

**Key Protocols**:
- Update `Phase5_Plan.md` after successful implementations
- Update `LEARNED.md` with new technical patterns
- Run `Schmekla.bat` to verify changes

---

### 2. Architect (Planner)
**File**: `schmekla-architect.md`
**Role**: Planning & Task Decomposition

| Responsibility | Description |
|----------------|-------------|
| Feature Planning | Design implementation approach |
| Task Breakdown | Split features into atomic tasks |
| Architecture Integrity | Ensure patterns are followed |
| Documentation | Maintain `ARCHITECTURE.md`, ADRs |

**Does NOT**: Write implementation code

**Output Example**:
```
Feature: Rubber Band Selection
├── Task 1: Track drag start (viewport.py)
├── Task 2: Draw selection rectangle
├── Task 3: Calculate selected elements
└── Task 4: Integrate with model
```

---

### 3. Coder (Senior Developer)
**File**: `schmekla-coder.md`
**Role**: Implementation Specialist

| Responsibility | Description |
|----------------|-------------|
| Code Implementation | Write/modify Python code |
| Environment Setup | venv, dependencies, pip |
| Bug Fixes | Debug and resolve issues |
| Progress Updates | Update tracking files after completion |

**Key Protocols**:
- After `pip install`, run `pip freeze > requirements.txt`
- Update `Phase5_Plan.md` when task complete
- Update `LEARNED.md` with new patterns

---

### 4. Researcher
**File**: `schmekla-researcher.md`
**Role**: Information Gathering & Analysis

| Responsibility | Description |
|----------------|-------------|
| Technical Research | API docs, library usage |
| Knowledge Synthesis | Summarize findings for team |
| Internal Search | Query local knowledge base first |
| Standards Lookup | Eurocodes, Tekla specs, IFC |

**Search Protocol**:
1. First: Check `knowledge/` folder, local files
2. Then: External documentation if needed

---

## Utility Agents

### 5. Code Reviewer
**File**: `code-reviewer.md`
**When to Use**: After writing/modifying code

| Checks | Priority |
|--------|----------|
| Security (API keys, injection) | CRITICAL |
| Code quality (functions >50 lines) | HIGH |
| Performance (O(n²) algorithms) | MEDIUM |
| Best practices (naming, docs) | MEDIUM |

---

### 6. Build Error Resolver
**File**: `build-error-resolver.md`
**When to Use**: Build fails, type errors

| Focus | Approach |
|-------|----------|
| TypeScript errors | Minimal type annotations |
| Import errors | Fix paths, install packages |
| Build failures | Configuration fixes |

**Key Rule**: Minimal diffs only, no refactoring

---

### 7. Refactor Cleaner
**File**: `refactor-cleaner.md`
**When to Use**: Dead code cleanup

| Actions | Tools |
|---------|-------|
| Find unused code | knip, depcheck, ts-prune |
| Remove duplicates | Grep analysis |
| Clean dependencies | npm audit |

**Key Rule**: Document all deletions in `DELETION_LOG.md`

---

### 8. E2E Runner
**File**: `e2e-runner.md`
**When to Use**: End-to-end testing needed

| Focus | Framework |
|-------|-----------|
| User journey tests | Playwright |
| Flaky test management | Quarantine pattern |
| Artifact capture | Screenshots, videos |

---

## Workflow Examples

### Example 1: New Feature Request

```
User: "Add rubber band selection"
    │
    ▼
Boss: Receives request, delegates to Architect
    │
    ▼
Architect: Plans feature, creates 4 tasks
    │
    ▼
Boss: Assigns tasks to Coder
    │
    ▼
Coder: Implements Task 1 → Task 2 → Task 3 → Task 4
    │
    ▼
Code Reviewer: Reviews changes (if needed)
    │
    ▼
Boss: Runs Schmekla.bat, verifies feature
    │
    ▼
Boss: Updates Phase5_Plan.md ✅, LEARNED.md
    │
    ▼
Boss: Reports success to User
```

### Example 2: Bug Fix

```
User: "Selection highlight doesn't work"
    │
    ▼
Boss: Delegates to Coder for investigation
    │
    ▼
Coder: Debugs, identifies issue, fixes code
    │
    ▼
Boss: Verifies fix with Schmekla.bat
    │
    ▼
Boss: Updates tracking files, reports to User
```

### Example 3: Build Failure

```
Coder: Reports build failure
    │
    ▼
Boss: Delegates to Build Error Resolver
    │
    ▼
Build Error Resolver: Minimal fixes applied
    │
    ▼
Boss: Verifies build passes, reports status
```

---

## Communication Patterns

### Boss ↔ User
- Receive high-level requests
- Report completion status
- Ask clarifying questions

### Boss ↔ Architect
- Request feature planning
- Receive task breakdown
- Approve design decisions

### Boss ↔ Coder
- Assign implementation tasks
- Receive completion reports
- Request bug fixes

### Architect → Coder
- Provide task specifications
- Reference existing patterns
- Define acceptance criteria

### Researcher → Architect/Coder
- Provide technical documentation
- Answer API questions
- Supply specifications

---

## Progress Tracking Files

| File | Updated By | When |
|------|------------|------|
| `Phase5_Plan.md` | Boss, Coder | After task completion |
| `knowledge/LEARNED.md` | Boss, Coder, Architect | New pattern discovered |
| `docs/ARCHITECTURE.md` | Architect | Structure changes |
| `IMPLEMENTATION_PLAN.md` | Boss | Phase milestones |

---

## Quick Reference

| Need | Agent |
|------|-------|
| Plan a feature | Architect |
| Write code | Coder |
| Research API/docs | Researcher |
| Fix build errors | Build Error Resolver |
| Review code quality | Code Reviewer |
| Remove dead code | Refactor Cleaner |
| Run E2E tests | E2E Runner |
| Orchestrate & track | Boss |

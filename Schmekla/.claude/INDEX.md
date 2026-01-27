# Schmekla Production Agents - Index

**Version**: 1.0.0
**Created**: 2026-01-27
**Status**: Production-Ready

---

## Agent Ecosystem Overview

```
                              ┌─────────────────────────┐
                              │      USER REQUEST       │
                              └───────────┬─────────────┘
                                          │
                              ┌───────────▼─────────────┐
                              │    schmekla-boss        │
                              │    (Orchestrator)       │
                              │    Model: Opus          │
                              │    Color: Red           │
                              └───────────┬─────────────┘
                                          │
           ┌──────────────────────────────┼──────────────────────────────┐
           │                              │                              │
           ▼                              ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│ schmekla-architect  │      │ schmekla-researcher │      │ schmekla-documenter │
│ (System Design)     │      │ (Investigation)     │      │ (Documentation)     │
│ Model: Opus         │      │ Model: Sonnet       │      │ Model: Haiku        │
│ Color: Blue         │      │ Color: Cyan         │      │ Color: Light Blue   │
└─────────┬───────────┘      └─────────────────────┘      └─────────────────────┘
          │
          │ Design Specs
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          IMPLEMENTATION LAYER                                │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│ schmekla-coder      │ schmekla-vtk        │ schmekla-ifc                    │
│ (General Code)      │ (UI/3D Specialist)  │ (IFC/Domain Expert)             │
│ Model: Sonnet       │ Model: Sonnet       │ Model: Sonnet                   │
│ Color: Green        │ Color: Orange       │ Color: Brown                    │
└─────────┬───────────┴─────────┬───────────┴─────────────────────────────────┘
          │                     │
          ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            QUALITY LAYER                                     │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│ schmekla-tester     │ schmekla-reviewer   │ schmekla-security               │
│ (Test Automation)   │ (Code Quality)      │ (Security Audit)                │
│ Model: Haiku        │ Model: Haiku        │ Model: Sonnet                   │
│ Color: Yellow       │ Color: Purple       │ Color: Dark Red                 │
└─────────────────────┴─────────────────────┴─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPPORT LAYER                                      │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ schmekla-debugger   │ schmekla-devops                                       │
│ (Troubleshooting)   │ (Release Management)                                  │
│ Model: Haiku        │ Model: Haiku                                          │
│ Color: Pink         │ Color: Gray                                           │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

---

## Agent Roster

| # | Agent Name | File | Model | Category | Purpose |
|---|------------|------|-------|----------|---------|
| 1 | schmekla-boss | `schmekla-boss.md` | Opus | Orchestration | Central command and coordination |
| 2 | schmekla-architect | `schmekla-architect.md` | Opus | Design | System architecture and planning |
| 3 | schmekla-researcher | `schmekla-researcher.md` | Sonnet | Investigation | Research and exploration |
| 4 | schmekla-coder | `schmekla-coder.md` | Sonnet | Implementation | General code implementation |
| 5 | schmekla-vtk | `schmekla-vtk.md` | Sonnet | Implementation | PyVista/VTK/Qt specialist |
| 6 | schmekla-ifc | `schmekla-ifc.md` | Sonnet | Implementation | IFC export and domain expert |
| 7 | schmekla-tester | `schmekla-tester.md` | Haiku | Quality | Test automation and coverage |
| 8 | schmekla-reviewer | `schmekla-reviewer.md` | Haiku | Quality | Code review and quality |
| 9 | schmekla-security | `schmekla-security.md` | Sonnet | Quality | Security auditing |
| 10 | schmekla-debugger | `schmekla-debugger.md` | Haiku | Support | Error resolution |
| 11 | schmekla-documenter | `schmekla-documenter.md` | Haiku | Support | Documentation maintenance |
| 12 | schmekla-devops | `schmekla-devops.md` | Haiku | Support | Build and release |

---

## Model Cost Optimization

| Model | Count | Use Case |
|-------|-------|----------|
| Opus ($$$$) | 2 | Complex reasoning: orchestration, architecture |
| Sonnet ($$$) | 5 | Domain expertise: coding, VTK, IFC, research, security |
| Haiku ($) | 5 | Pattern-based: testing, review, debug, docs, devops |

**Cost Reduction**: Moving routine tasks from Opus to Sonnet/Haiku reduces costs by ~60%

---

## Quality Gates Reference

| Gate | Name | Owner | When |
|------|------|-------|------|
| QG-01 | Requirements Validation | Architect | Before design |
| QG-02 | Design Review | Boss | Before implementation |
| QG-03 | Build Verification | Coder | After code changes |
| QG-04 | Code Review | Reviewer | Before merge |
| QG-05 | Test Coverage | Tester | Before feature complete |
| QG-06 | Security Scan | Security | Before release |
| QG-07 | Documentation Check | Documenter | Before feature complete |
| QG-08 | Application Verification | Boss | Before task closure |

---

## Workflow Quick Reference

### New Feature
```
Boss → Architect → [Coder/VTK/IFC] → Tester → Reviewer → Boss
```

### Bug Fix
```
Boss → Researcher → Coder → Tester → Reviewer → Boss
```

### Release
```
Boss → Tester → Security → Reviewer → Documenter → DevOps → Boss
```

---

## File Listing

```
production-agents/
├── INDEX.md                    # This file
├── schmekla-boss.md           # Orchestrator (Opus)
├── schmekla-architect.md      # System Designer (Opus)
├── schmekla-researcher.md     # Investigation (Sonnet)
├── schmekla-coder.md          # General Implementation (Sonnet)
├── schmekla-vtk.md            # VTK/PyVista Specialist (Sonnet)
├── schmekla-ifc.md            # IFC Domain Expert (Sonnet)
├── schmekla-tester.md         # Test Automation (Haiku)
├── schmekla-reviewer.md       # Code Review (Haiku)
├── schmekla-security.md       # Security Audit (Sonnet)
├── schmekla-debugger.md       # Troubleshooting (Haiku)
├── schmekla-documenter.md     # Documentation (Haiku)
└── schmekla-devops.md         # Build/Release (Haiku)
```

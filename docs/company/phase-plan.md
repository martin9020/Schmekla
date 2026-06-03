# Schmekla Phase Plan

## Governance Model

Every phase has:

- A named owner.
- A written acceptance checklist.
- Tests or a documented test gap.
- Code review before closure.
- Release verification before user-facing milestone claims.

Current Paperclip roles:

- CEO: owns mission, product gates, task decomposition, and escalation.
- Lead Engineer: owns implementation execution.
- Code Reviewer: owns quality review and regression risk review.
- Release Engineer: owns environment, packaging, deployment, and release gates.

## Phase 0: Company Onboarding And Baseline

Owner: CEO

Deliverables:

- `docs/company/mission.md`
- `docs/company/onboarding.md`
- `docs/company/capability-matrix.md`
- `docs/company/phase-plan.md`
- `docs/company/risk-register.md`

Acceptance:

- Repository structure and current-state risks are documented.
- Public-source boundary is documented.
- First two downstream tasks are created for Lead Engineer.
- The kickoff issue is handed to review or marked done only after artifacts are written.

## Phase 1: Repository Current-State Assessment

Owner: Lead Engineer

Goal: turn the onboarding snapshot into an engineer-verified baseline.

Scope:

- Establish reproducible Python environment and test command.
- Run or fix the existing tests only enough to get a trustworthy baseline.
- Inventory source modules, entry points, dependency mismatches, stale docs, and corrupted files.
- Produce a short current-state assessment with blockers and recommended first fixes.

Acceptance:

- Test command is documented with exact Python version and environment.
- Existing tests either pass or failures are triaged with file-level causes.
- No unrelated code rewrites.
- Findings are reviewed by Code Reviewer.

## Phase 2: First Deployable Vertical Slice Architecture

Owner: Lead Engineer

Goal: design the smallest production-worthy slice from model creation to IFC validation.

Scope:

- Define the frame example model and required object set.
- Specify persistence contract for that object set.
- Specify IFC export contract and validation procedure.
- Define automated and manual verification steps.
- Identify required source changes and test files.

Acceptance:

- Architecture plan has exact file paths, test targets, and review gates.
- Plan excludes advanced features not needed for the slice.
- Code Reviewer signs off before implementation.
- Release Engineer confirms environment and validation tooling path.

## Phase 3: Vertical Slice Implementation

Owner: Lead Engineer

Goal: implement and verify the first deployable slice.

Scope:

- Add focused tests first for model round-trip and IFC export behavior.
- Fix only the code required for the slice.
- Add or update docs for running the slice.
- Produce an IFC validation artifact.

Acceptance:

- Tests pass in a clean environment.
- IFC artifact validates with the chosen automated checker or has a documented checker limitation.
- Manual viewer/Tekla import results are recorded.
- Code Reviewer approves the diff.

## Phase 4: Release Hardening

Owner: Release Engineer

Goal: make the slice reproducible outside the development shell.

Scope:

- Validate installer/launcher.
- Pin Python version guidance.
- Document clean-machine setup.
- Add release checklist and artifact naming.

Acceptance:

- Fresh environment can install dependencies and run tests.
- Application launches or known launch blockers are documented.
- Release notes accurately describe supported and unsupported behavior.

## Phase 5: Product Expansion

Owner: CEO with Lead Engineer

Candidate tracks:

- Connection semantics and IFC/export strategy for bolts/welds.
- Drawing and report generation.
- Selection/filtering and production UI workflows.
- AI plan import with strict command review and safety controls.
- Profile/material catalog governance.

Each track needs its own brainstorming spec and implementation plan before code changes.

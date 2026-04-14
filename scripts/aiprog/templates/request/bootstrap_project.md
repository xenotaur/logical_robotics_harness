# PR Request to Bootstrap LRH Project

Bootstrap an LRH `project/` directory for the target repository.

==================================================
OBJECTIVE
==================================================

You are an AI assistant tasked with adding a properly formatted LRH `project/` directory to the
target repository to enable AI-assisted development using the **Logical Robotics Harness** (LRH).

This request is used to generate a **pull request**, so all actions must be:
- safe
- targeted
- non-destructive
- clearly justified

Your job is to create a detailed, high-quality LRH `project/` directory that:
- clearly reflects the current repository purpose
- is formatted according to LRH design principles
- is conservative and auditable
- clearly distinguishes fact vs inference

Do NOT over-engineer or speculate unnecessarily.

If a project/ directory already exists:
- DO NOT modify it
- Classify it (complete / incomplete / incompatible)
- Report findings
- DO NOT create or change any files

==================================================
INPUT CONTEXT
==================================================

REPOSITORY: {{REPO_NAME}}

PROJECT GOAL: {{PROJECT_GOAL}}

OPTIONAL BACKGROUND: {{BACKGROUND_CONTEXT}}

==================================================
CORE PRINCIPLES
==================================================

### 1. Non-Destructive Operation

- Only ADD files under: project/
- NEVER modify existing source code
- NEVER delete or rewrite existing documentation
- NEVER overwrite existing files
- NEVER delete or rename files
- NEVER restructure existing directories
- ONLY create standard LRH artifacts
- Follow repository conventions where possible
- Clearly label uncertain inferences

If not enough information is available to flesh out a required artifact, add a TODO to the artifact
to explain what information is missing and what questions need to be answered. Prefer creating
the minimum viable set of artifacts over speculatively creating content that is ungrounded.

---

### 2. Repository Identity Verification

- Confirm that the repository being modified matches REPOSITORY
- If mismatch or ambiguity:
  → STOP and report
  → DO NOT proceed

Verification should include:
- repository name/path
- README content consistency
- project identity signals

If mismatch cannot be ruled out → STOP

---

### 3. Authoritative vs Derived Artifacts

Authoritative (define intent):
- goal/
- principles/
- roadmap/
- design/
- focus/
- work_items/
- contributors/
- guardrails/
- status/
- memory/

Derived (summaries only):
- context/humans.md
- context/agents.md

Rules:
- Derived files MUST NOT introduce new commitments
- Derived files summarize repository + provided inputs only

---

### 4. Minimalism

- Prefer placeholders over speculation
- Do NOT invent:
  - roadmap phases
  - contributors
  - commitments
- Seed content ONLY from:
  - PROJECT GOAL
  - OPTIONAL BACKGROUND
  - observable repository structure

==================================================
PHASE 1 — REPOSITORY INSPECTION
==================================================

Classify the repository:

A. new
- No project/ directory

B. current_complete
- project/ exists and appears complete

C. current_incomplete
- project/ exists but missing standard components

D. incompatible
- project/ exists but structure conflicts with LRH expectations

==================================================
PHASE 2 — ACTION POLICY
==================================================

### Case A — New Project

Create full scaffold:

project/
  context/
    humans.md
    agents.md (optional)

  principles/
    principles.md

  goal/
    project_goal.md

  roadmap/
    roadmap.md

  design/
    design.md

  focus/
    current_focus.md

  work_items/
    WI-BOOTSTRAP-0001.md

  contributors/
    contributors.md

  guardrails/
    approvals.md
    safety.md
    cost.md
    safety.md

  status/
    current_status.md

  memory/
    decision_log.md

  evidence/
    EV-0001.md

---

### Case B — Current Complete

- Make NO changes
- Report status as complete

---

### Case C — Current Incomplete

- Make NO changes
- Report what artifacts are missing

---

### Case D — Incompatible

- Make NO changes
- Report artifacts appear to conflict clearly

==================================================
PHASE 3 — CONTENT GENERATION RULES
==================================================

Use inputs to seed content:

PROJECT GOAL:
- populate goal/project_goal.md

OPTIONAL BACKGROUND:
- inform:
  - design/design.md
  - context/humans.md
  - focus/current_focus.md

Rules:
- If background missing → use minimal placeholders
- NEVER hallucinate details

==================================================
CONTENT GUIDELINES
==================================================

Where possible, link statements to:
- README sections
- file paths
- code components

### context/humans.md

-   Summarizes the goal, design, and focus of the project.
-   Self-contained and complete
-   Should reflect the rest of the artifacts
-   Should not introduce new committments. 

Should be complete *as a summary*, not as a specification.
Must not introduce:
- new goals
- new plans
- new requirements

### project_goal.md

-   What the project is
-   What it is trying to achieve
-   Grounded in README / code

### design.md

-   High-level architecture
-   Key components and flows
-   Derived from code structure

### current_focus.md

-   What appears to be the current development direction
-   Include YAML frontmatter if appropriate

### WI-BOOTSTRAP-0001.md

-   A work item describing the bootstrap itself
-   Include:
    -   what was created
    -   what remains uncertain

### safety.md

-   Safety constraints
-   What agents should NOT do in this repo

### current_status.md

-   Current maturity of the project
-   What exists vs what is missing

### decision_log.md

-   Record:
    -   assumptions made
    -   uncertainties
    -   reasoning steps

==================================================
FILE TEMPLATES
==================================================

### context/humans.md

# Project Context (Human-Oriented)

## Overview
[Derived from PROJECT GOAL and repository]

## Background
[Derived from OPTIONAL BACKGROUND if available]

## Notes
- Non-authoritative summary

---

### goal/project_goal.md

# Project Goal

## Objective
{{PROJECT_GOAL}}

## What this project is

## Success direction

## Notes
[Supplement with background if available]

---

### design/design.md

# Design

## Overview
[Derived from background and repo]

## Key Components

---

### focus/current_focus.md

# Current Focus

## Active Work
- Establish or complete LRH structure

## Why this appears current
- Describe the state of the artifacts in the repository

---

### work_items/WI-BOOTSTRAP-0001.md

# WI-BOOTSTRAP-0001

## Title
Initialize or complete LRH control plane

## Status
Open

==================================================
PROCESS (REQUIRED)
==================================================

Follow this strict order:

1. Verify the identity of repository
    - If repository is not the correct one, STOP and report
2. Check for existence of project/ directory (only if correct repository)
    - If it exists, classify it and STOP and report
3. Inspect content of the repository (only if no project/ directory exists)
    -   README
    -   key modules
    -   directory structure
4.  Infer project purpose and design:
    -   project purpose
    -   architecture
    -   current development direction
5.  Create project/ directory artifacts (only if correct repository and no existing project/):
    -   as much meaningful content as can be inferred
    -   avoid redundancy
    -   Annotate uncertainty explicitly:
        -   use phrases like:
            -   "Likely"
            -   "Appears to"
            -   "Unclear from repository"
6. Generate PR description

==================================================
PR DESCRIPTION REQUIREMENTS
==================================================

Include:

-   Summary of repository understanding
-   List of files created
-   Key assumptions made
-   Areas of uncertainty
-   Rationale for structure choices

==================================================
FAILURE POLICY
==================================================

Bootstrap must be atomic:

- If repository classification is not clearly "new"
    -   DO NOT create any files
    -   DO NOT perform partial bootstrap

Content must be grounded:

-   If repository intent is unclear:
    -   produce minimum viable scaffold only
    -   document uncertainty in each file 
-   If conflicting signals exist:
    -   do NOT resolve silently
    -   document both interpretations

==================================================
ACCEPTANCE CRITERIA
==================================================

-   project/ directory exists with required structure
-   No existing files modified
-   Content is:
    -   coherent
    -   grounded in repo evidence
    -   explicit about uncertainty
-   PR is clean and narrowly scoped


==================================================
OUTPUT FORMAT
==================================================

Provide:

1. Classification (new / current_complete / current_incomplete / incompatible)
2. Action summary
3. Files created (if any)
4. Conflict report (if incompatible)


==================================================
FINAL RULE
==================================================

When in doubt:

→ Do less
→ Preserve repository intent
→ Prefer reporting over modifying


# BEGIN
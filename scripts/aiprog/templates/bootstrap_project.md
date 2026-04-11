# PR Request to Bootstrap LRH Project

Bootstrap an LRH `project/` directory for the target repository.

==================================================
INPUT CONTEXT
==================================================

REPOSITORY: {{REPO_NAME}}

PROJECT GOAL: {{PROJECT_GOAL}}

OPTIONAL BACKGROUND: {{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Create a minimal, high-quality LRH `project/` directory that:

-   reflects the current repository purpose
-   aligns with LRH design principles
-   is conservative and auditable
-   clearly distinguishes fact vs inference

Do NOT over-engineer or speculate unnecessarily.

==================================================
CONSTRAINTS (STRICT)
==================================================

-   Do NOT modify existing source code
-   Do NOT delete or rewrite existing documentation
-   Only ADD files under: project/
-   Follow repository conventions where possible
-   Prefer minimal viable structure over completeness
-   Clearly label uncertain inferences

==================================================
REQUIRED OUTPUT STRUCTURE
==================================================

Create the following structure:

project/ goal/ project_goal.md design/ design.md focus/ current_focus.md
work_items/ WI-BOOTSTRAP-0001.md guardrails/ agent_guardrails.md status/
current_status.md memory/ decision_log.md

==================================================
CONTENT GUIDELINES
==================================================

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

### agent_guardrails.md

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
PROCESS (REQUIRED)
==================================================

1.  Inspect repository:
    -   README
    -   directory structure
    -   key modules
2.  Infer:
    -   project purpose
    -   architecture
    -   current development direction
3.  Create project/ artifacts:
    -   minimal but meaningful content
    -   avoid redundancy
4.  Annotate uncertainty explicitly:
    -   use phrases like:
        -   "Likely"
        -   "Appears to"
        -   "Unclear from repository"

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

-   If repository intent is unclear:
    -   produce minimal scaffold only
    -   document uncertainty
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

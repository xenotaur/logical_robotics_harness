# Development Agenda for LRH

The following document contains a list of tasks that are currently being worked on or are planned to be worked on based on the agenda of the human user. This currently is manually generated rather than automatically generated.

## Human-Initiated Streams of Work

There are several streams of work initiated by the human user.

* LRH Serve: Provide a visual dashboard which can display the status of LRH-driven development.
  * LRH Meta Dashboard: Show all the registered projects and their status.
    * LRH Meta Schema: Update the schema to support local/remote projects.
    * LRH Meta Visual Language: Define a visual language for LRH.
    * LRH Meta safe-default local viewer/workbench baseline is mostly landed but we are working meta/triage extensions as explicit follow-ons.
* LRH Execution Tree: Define a tree of planning nodes and leaf executable nodes that will control the development process on a project.
  * LRH Workstreams: Define a workstream abstraction which is the intermediate layer of execution betwen the top-level project goals and the low-level work items that are executed.
  * LRH Execution System: Implement the 'Huge Loop' (staged bounded execution-framework sequence) which controls the execution of prompts in coordinaton with external tools.
    * Work Item to Prompt Interface: Enable kicking off the Huge Loop from a work item, which involves both work item readiness and run packet generation.
  * LRH External Interface: Implement a system which enables us to capture what work is ongoing in external systems even if not with the LRH tree.
    * LRH Activity Lanes: Define a way to represent ongoing human work in an external system as activities within LRH's meta dashboard.
        * [LRH Activity Lanes and Observational Dashboard](../design/proposals/proposed/activity-lanes-and-observational-dashboard.md) 
    * LRH Conversation System: Define a way to represent conversations durably but also securely; has a storage layer and other abstractions.
      * LRH Chat PDF Import System: Import chat content from a PDF.

## Active Streams of Work in the Project Control Plane.

There are other outstanding items that aren't yet captured above.

- Execution Framework (staged)
  - Next package (near-term): Layer 2 durable manual run-state tracking
    - define `project/runs/<RUN-ID>/` artifact layout (`packet.yaml`, `state.yaml`, `events.jsonl`, `prompts/`, `evidence/`, `report.md`)
    - preserve manual-mode parity and explicit human gates
  - Readiness pathway follow-ons
    - deterministic `lrh work-items readiness`
    - assistive `lrh request ready-work-item`
    - workflow docs for validate/audit/readiness/prompt/report boundaries
  - Deferred design follow-ons (after Layer 2)
    - agent branch containment policy support
    - GitHub PR/CI observation adapter design
    - bounded stabilization loop design

- CI Capability Scaffolding (adjacent support stream)
  - refresh CI request templates using the playbook
  - evaluate CI skill prototype after additional non-LRH dogfooding
  - reassess reusable CI template fragments based on evidence

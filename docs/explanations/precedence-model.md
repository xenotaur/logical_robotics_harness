# Precedence model

Precedence answers a practical question: when multiple project-control layers say something about
scope, authority, or constraints, which layer controls interpretation?

LRH's canonical precedence semantics are defined by the accepted decision record in
[`project/memory/decisions/precedence_semantics.md`](../../project/memory/decisions/precedence_semantics.md).
This page is only an explanation of that model. See
[`design.md` §14 "Decision-record tiers"](../../project/design/design.md#decision-record-tiers)
for why this decision is a promoted single-topic file rather than an entry
in `project/memory/decision_log.md`.

## Resolution order

LRH resolves from broad intent toward narrow execution context:

1. principles;
2. project goal;
3. roadmap;
4. current focus;
5. work items;
6. guardrails;
7. runtime invocation.

Earlier layers are higher authority. Later layers refine and narrow the work; they do not override
higher layers.

## How to think about the layers

A useful mental model is a funnel:

```text
broad intent
  ↓
project-specific goal
  ↓
planned direction
  ↓
near-term focus
  ↓
concrete work items
  ↓
subtractive guardrails
  ↓
runtime selection of an allowed subset
```

The funnel can get narrower as information becomes more operational. It should not widen again at
a lower layer.

## What lower layers may do

Lower-authority layers may:

- choose a subset of the roadmap for the current focus;
- turn current focus into concrete work items;
- mark a work item blocked or out of scope;
- select one allowed work item for a particular run;
- add narrower acceptance or evidence expectations.

Lower-authority layers may not:

- contradict principles;
- redefine the project goal;
- make out-of-focus work authoritative merely because a runtime prompt asks for it;
- reintroduce work that guardrails removed;
- treat memory notes as resolver authority.

## Guardrails are subtractive

Guardrails constrain actions through safety, cost, optics, and approval boundaries. They can block
or remove candidates from consideration, but they do not define the positive project plan on their
own.

For example, a guardrail can say that a class of production write needs approval. It does not by
itself create a work item to perform that write.

## Runtime invocation is narrowing-only

A command, prompt, or run request may select an allowed subset of the loaded project state. It
cannot override higher layers or re-add candidates excluded by guardrails.

If runtime input conflicts with current focus, LRH should treat that as a consistency issue rather
than silently pretending the loaded focus changed.

## Memory is informative, not authoritative

The `project/memory/` tree records decisions, lessons, questions, and other context. Memory can be
important for understanding why the project is shaped a certain way, but it is not a precedence
layer in resolver computation.

Accepted decisions may define canonical behavior, but the resolver chain itself does not treat
memory as another scope layer between status and runtime.

## Maintenance rule

Precedence is a synchronized contract. Any future change to precedence semantics must update the
canonical decision record, the implementation, and tests in the same change set.

Authoritative sources:

- [canonical precedence decision](../../project/memory/decisions/precedence_semantics.md);
- [precedence implementation](../../src/lrh/control_plane/precedence.py);
- [precedence tests](../../tests/control_plane_tests/precedence_test.py);
- [repository specification precedence section](../../project/design/repository_spec.md#precedence);
- [decision-record tiers](../../project/design/design.md#decision-record-tiers)
  (`design.md` §14).

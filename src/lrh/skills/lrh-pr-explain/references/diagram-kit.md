# Diagram kit

A figure goes in `briefing.figures[]` with raw `html`. The template already
styles everything below, in both light and dark themes, so use these classes
instead of inline colors. Never use a literal color.

## When a figure earns its place

Draw one only when it shows a mechanism that prose would make the reader
reconstruct in their head. Good reasons:

- A new module or layer that several entry points now route through
  (architecture map).
- A new multi-step user flow that crosses processes or machines
  (walkthrough).
- Behavior that depends on a combination of two states (transition matrix).
- A mapping between two coordinate systems, such as host and container
  paths (path mapping).

Skip figures for small or purely local changes. Zero to three per briefing.
Every box, arrow, and cell must match the code; mark new things as new.

## Shared rules

- Wrap anything wider than about 400px in `<div class="scroll">` so it
  scrolls inside the figure on phones; give the SVG or grid a `min-width`.
- SVG: use a `viewBox` about 960 wide, `width="100%"`, `role="img"`, and an
  `aria-label` that states what the diagram shows. Leave room inside the
  viewBox for the outermost labels.
- Escape `<`, `>`, and `&` in any text you write into the HTML.
- Never paste PR text (commit messages, descriptions, comments) into figure
  HTML; write your own labels.

## Architecture map (SVG)

Classes:

| Class | Use |
|---|---|
| `svg-box` | A component box (`<rect rx="8">`). Add `entry` for entry points and inputs, `new` for things this PR adds, `warn` for a component a review note is about. |
| `svg-group` | Dashed outline grouping boxes from one module. |
| `svg-t` | Box title (13px, bold). |
| `svg-s` | Box subtitle (11px, muted). |
| `svg-m` | Monospace label for commands, paths, identifiers. |
| `svg-g` | Group label (accent, small caps feel). |
| `svg-line` | Connector path; add `dash` for "carries config/data" edges. |

The template defines an arrowhead marker with id `ah`; use
`marker-end="url(#ah)"` and stop the path about 4px short of the target box.

```html
<div class="scroll">
<svg viewBox="0 0 960 200" width="100%" style="min-width:820px" role="img"
     aria-label="tw activate calls cli.py, which builds an EnvironmentContext">
  <rect x="20" y="30" width="190" height="56" rx="8" class="svg-box entry"/>
  <text x="34" y="54" class="svg-m">tw activate NAME</text>
  <text x="34" y="72" class="svg-s">sourced shell helper</text>
  <rect x="250" y="30" width="210" height="56" rx="8" class="svg-box new"/>
  <text x="264" y="54" class="svg-t">cli.py</text>
  <text x="264" y="72" class="svg-m">environment prepare | enter</text>
  <path d="M210 58 H246" class="svg-line" marker-end="url(#ah)"/>
</svg>
</div>
```

Layout: columns left to right in call order (entry points, handlers, shared
model, implementations, external tools). Route connectors orthogonally
(`H`/`V` segments) and keep them out of box interiors.

## Walkthrough (swimlanes)

A CSS grid with one row per actor (host shell, CLI, container, service) and
numbered steps placed by column. Set `--cols` to the number of step columns.

```html
<div class="scroll">
  <div class="lanes" style="--cols:6" role="list">
    <div class="lane-label" style="grid-row:1">Your host shell</div>
    <div class="step guard" style="grid-row:1;grid-column:2" role="listitem">
      <span class="n">1</span><b>tw activate DevA</b><br>Refuses if already inside a container.</div>
    <div class="lane-label" style="grid-row:2">taurworks CLI</div>
    <div class="step" style="grid-row:2;grid-column:3" role="listitem">
      <span class="n">2</span><b>environment prepare</b><br>Runs <code>devcontainer up</code>.</div>
    <div class="lane-label" style="grid-row:3">Dev Container</div>
    <div class="step you" style="grid-row:3;grid-column:4 / span 2" role="listitem">
      <b>You work here</b><br>Interactive shell at the mapped directory.</div>
  </div>
</div>
<div class="callout">If any step fails, the host shell is left unchanged.</div>
```

Step modifiers: `guard` (red left edge, a refusal or check), `you` (dashed,
where the user acts). Number only steps that run in sequence. A `callout`
under the grid states the failure or invariant rule.

## Transition matrix (table)

Rows are the current state, columns the next action or target. Cells:
`y` allowed (green), `n` refused (red), `w` allowed with a caveat (amber).
Inside a cell, `<span class="mk">✓</span>` (or ✗, !) leads, then a short
reason; optional tags: `<span class="t">tested</span>` when a test covers
that cell, `<span class="newb">changed</span>` when this PR changed it.

```html
<div class="matrix-wrap"><table class="matrix">
  <thead><tr><th></th><th>→ Host project</th><th>→ Conda project</th></tr></thead>
  <tbody>
    <tr><th class="row">Conda project<small>host shell with Conda env</small></th>
      <td class="y"><span class="mk">✓</span>Now runs <code>conda deactivate</code> first.<br><span class="newb">changed</span></td>
      <td class="y"><span class="mk">✓</span>Activates the new env.<br><span class="t">tested</span></td></tr>
    <tr><th class="row">Inside a container shell</th>
      <td class="n"><span class="mk">✗</span>Refused. Exit first.</td>
      <td class="n"><span class="mk">✗</span>Refused.<br><span class="t">tested</span></td></tr>
  </tbody>
</table></div>
```

Only mark a cell `tested` when you found the test that exercises it.

## Path mapping

```html
<div class="eyebrow">Path mapping for <code>working_dir = "backend"</code></div>
<div class="pathmap">
  <span class="lbl">Host</span><code>&lt;project_root&gt;/backend</code>
  <span class="lbl">Container</span><code>&lt;remoteWorkspaceFolder&gt;/backend</code>
</div>
```

## Combining

One figure may hold several blocks (for example a swimlane grid followed by
a callout, or a path mapping after a matrix). Put a `caption` on the figure
for what the colors or dashes mean.

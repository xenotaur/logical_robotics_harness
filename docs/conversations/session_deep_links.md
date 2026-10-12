# Open an agent session from a pointer

Use this guide when an execution record names the agent session that did its
work and you want a link that opens that session in its desktop app. LRH stores
the session as a `scheme:identifier` pointer, such as
`claude-app:<host-uuid-stem>`, and can turn it into a deep link on demand.

```bash
lrh sessions deeplink claude-app:a6e3e7d1-6dca-4a75-999f-73b646ceb1fa
# claude://claude.ai/epitaxy/local_a6e3e7d1-6dca-4a75-999f-73b646ceb1fa

open "$(lrh sessions deeplink codex-app:01a032cd-cef2-73c0-9714-b61b36ae4513)"
```

The command prints the link and exits `0`, or prints a message to stderr and
exits `1` when no link is known for the pointer. It reads only the pointer
string: it does not look up the session, read any transcript, or contact the
network. See the [`lrh sessions` CLI reference](../reference/cli/sessions.md).

## Which sessions have a link

| Pointer | Link | Status |
|---|---|---|
| `claude-app:<host-uuid-stem>` | `claude://claude.ai/epitaxy/local_<uuid>` | Verified by hand with `open`. The `epitaxy` route is undocumented by Anthropic and may change. |
| `codex-app:<thread-uuid>` | `codex://threads/<uuid>` | Verified by hand with `open`; this is the link the Codex desktop UI's Copy Deeplink action produces. |
| `antigravity-app:<id>` | none | Unknown. The app registers `antigravity://` and `antigravity-ide://` URL schemes, but no conversation route has been found. |
| `pending`, `none`, other schemes | none | No session to open. |

Claude CLI (terminal) sessions have no URL scheme, so they cannot be linked.
Links open sessions that live in the desktop app on the same machine; they do
not work from another computer, or for sessions that no longer exist.

## Limits to know about

- **Best-effort.** A route can change without notice. LRH treats the pointer as
  the durable record and derives the link at display time; it never stores the
  link.
- **No guessing.** A pointer the definition does not recognize, with an id that
  is not a UUID, gets no link rather than a made-up one.
- **Host ids versus child ids.** Claude host ids and child ids are both bare
  UUIDs, and only `project/sessions/index.jsonl` tells them apart. The helper
  checks the id's shape only, so the guarantee sits with whoever writes the
  pointer: only confirmed host ids become `claude-app:` pointers.

## Where the routes are defined

The supported routes live in one file,
[`src/lrh/conversations/session_links.json`](../../src/lrh/conversations/session_links.json):
each vendor's pointer prefix, link scheme, host, path template and id shape,
plus the accept and reject examples the tests run. The Python helper,
`lrh.conversations.deeplink.link_for`, reads that file, and the LRH Console's
link allowlist is meant to be built from the same file so the two cannot drift.
To change or add a route, edit that file and its examples, not the code.

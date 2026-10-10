# tools-modular

A pluggable-module version of the 45dgof8 tools hub. The whole site is assembled
at runtime from the folders in `modules/`: each module folder that contains a
`module.py` becomes a live tool/page/route.

## How modules work

Drop a folder into `modules/`, add a `module.py`, restart the server - the tool
appears. Delete the folder and restart - it is gone (route and index card).

A `module.py` exposes a `MODULE` dict and one or both functions:

```python
MODULE = {
    "kind": "tool",            # "tool" | "page" | "app" | "slot"
    "slug": "clock",           # route becomes /tools/<slug>
    "name": "Clock",
    "icon": "clock",
    "desc": "Short description for the index card",
    "title": "Clock",          # optional, page <title>/heading
    "subtitle": "...",         # optional
    "meta_desc": "...",        # optional, SEO meta description
}

def page():
    """HTML fragment, rendered inside the shared LAYOUT (kind tool/page)."""
    return "<div>...</div>"
```

### Kinds

- **`tool`** - appears in the tools grid; `page()` fragment wrapped in the shared
  LAYOUT; mounted at `/tools/<slug>`.
- **`page`** - like `tool` but not listed in the tools grid (e.g. privacy page).
- **`app`** - ships a **complete standalone HTML document** via `full_page()`
  (its own `<head>`, styles, scripts). Served as-is, not wrapped in LAYOUT.
  Example: `modules/orb/` (the Decision Orb).
- **`slot`** - no route. Its `slot_after()` output is injected wherever a page or
  app contains the `<!--SLOT_AFTER-->` marker. Used for cross-page content such
  as ads. Disabled slots simply return `""`.

### Slot injection

Pages and apps may place the literal marker `<!--SLOT_AFTER-->` (on its own
line). The server replaces it with the concatenated output of every enabled
`slot` module. When no slot produces content, the marker line collapses to
nothing, so output stays byte-identical to the un-instrumented document.

## Layout of the repo

- `modules/<name>/module.py` - one file per pluggable module (this is the part
  that is tracked).
- `modules/orb/orb.html` - the Decision Orb full document (kind `app`).
- `tools-server.py` - the Flask host. **Not tracked** (see `.gitignore`): it
  contains internal service topology and is kept local-only, mirroring
  `tools/tools-server.py`.

## Run locally (preview)

```bash
python3 tools-server.py 5007   # preview port; live monolith stays on 5006
```

Set `TOOLS_SECRET_KEY` in the environment for a stable session key; otherwise a
random per-restart key is used (fine for local preview).

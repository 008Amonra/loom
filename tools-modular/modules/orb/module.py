"""Module: orb (Decision Orb) - kind "app".

Ships a complete standalone HTML document (modules/orb/orb.html) instead of a
fragment embedded in the shared LAYOUT - the orb is a full-screen app with its
own styles, tabs and scripts.

On/off: delete this folder (or rename module.py) + restart = /tools/orb gone and
its card disappears from the index. Drop it back = it returns.
Plug-in: the document contains a SLOT_MARKER (<!--SLOT_AFTER-->) that the server
replaces with the output of every enabled slot module (e.g. the ads module).
"""

from pathlib import Path

HERE = Path(__file__).parent

MODULE = {
    "kind": "app",
    "slug": "orb",
    "name": "Decision Orb",
    "icon": "orb",
    "desc": "Sci-fi oracle + lottery generator for CH, EU, Finland, US & more - plus an AI research module",
    "title": "Decision Orb",
    "subtitle": "Sci-fi oracle + lottery generator",
    "meta_desc": "Decision Orb - a sci-fi oracle and lottery number generator (CH, EU, Finland, US and more) with an AI research module. Pull, shake or fling to draw.",
}


def full_page():
    return (HERE / "orb.html").read_text(encoding="utf-8")

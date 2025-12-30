bl_info = {
    "name": "Graph Monkey",
    "author": "Pluglug",
    "version": (0, 10, 0),
    "blender": (2, 80, 0),
    "location": "Graph Editor",
    "description": "Animation workflow toolkit for Graph Editor. Keyboard-driven keyframe editing.",
    "doc_url": "https://github.com/Pluglug/graph_monkey",
    "category": "Animation",
    "license": "GPL",
}

use_reload = "addon" in locals()
if use_reload:
    import importlib

    importlib.reload(locals()["addon"])
    del importlib

from . import addon

addon.init_addon(
    module_patterns=[
        "constants",
        "preferences",
        "keymap_manager",
        "operators.*",
        "ui.*",
        "utils.*",
    ],
    use_reload=use_reload,
)


def register():
    addon.register_modules()


def unregister():
    addon.unregister_modules()

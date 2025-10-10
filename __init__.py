bl_info = {
    "name": "Graph Monkey",  # Monkey Keyframe, Graph Monkey
    "author": "Pluglug",
    "version": (0, 9, 0),
    "blender": (2, 80, 0),
    "location": "Graph Editor",
    "description": "Move keyframe selection in the Graph Editor. and more",
    "warning": "Bananas required",
    "wiki_url": "https://github.com/Pluglug/MonKey/blob/main/README.md",
    "category": "Animation",
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

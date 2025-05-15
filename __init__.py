bl_info = {
    "name": "MonKey",  # Monkey Keyframe, Graph Monkey
    "author": "Pluglug",
    "version": (0, 7, 0),
    "blender": (2, 80, 0),
    "location": "Graph Editor",
    "description": "Move keyframe selection in the Graph Editor",
    "warning": "It'll explode",
    "wiki_url": "",
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
        "operators.*",
        "utils.*",
        "constants",
        "keymap",
        "overlay",
        "preferences",
    ],
    use_reload=use_reload,
)


def register():
    addon.register_modules()

def unregister():
    addon.unregister_modules()

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
from .keymap_manager import keymap_registry

addon.init_addon(
    module_patterns=[
        "constants",
        "keymap",
        "overlay",
        "preferences",
        "operators.*",
        "ui.*",
        "utils.*",
    ],
    use_reload=use_reload,
)


def register():
    addon.register_modules()
    keymap_registry.apply_keymaps()


def unregister():
    keymap_registry.unregister_keymaps()
    addon.unregister_modules()

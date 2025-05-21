import bpy
from .utils.logging import get_logger

# from . addon import prefs, ADDON_ID
# from . debug import log, DBG_PREFS

log = get_logger(__name__)

addon_keymaps = []


def register_keymaps():

    dir_map = {
        "upward": "W",
        "downward": "S",
        "forward": "D",
        "backward": "A",
    }

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name="Graph Editor", space_type="GRAPH_EDITOR")

    # Upward
    kmi = km.keymap_items.new(
        "graph.monkey_vertically", type=dir_map["upward"], value="PRESS", alt=True
    )
    kmi.properties.direction = "upward"
    kmi.properties.extend = False

    # Upward Extend
    kmi = km.keymap_items.new(
        "graph.monkey_vertically",
        type=dir_map["upward"],
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "upward"
    kmi.properties.extend = True

    # Downward
    kmi = km.keymap_items.new(
        "graph.monkey_vertically", type=dir_map["downward"], value="PRESS", alt=True
    )
    kmi.properties.direction = "downward"
    kmi.properties.extend = False

    # Downward Extend
    kmi = km.keymap_items.new(
        "graph.monkey_vertically",
        type=dir_map["downward"],
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "downward"
    kmi.properties.extend = True

    # Forward
    kmi = km.keymap_items.new(
        "graph.monkey_horizontally", type=dir_map["forward"], value="PRESS", alt=True
    )
    kmi.properties.direction = "forward"
    kmi.properties.extend = False

    # Forward Extend
    kmi = km.keymap_items.new(
        "graph.monkey_horizontally",
        type=dir_map["forward"],
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "forward"
    kmi.properties.extend = True

    # Backward
    kmi = km.keymap_items.new(
        "graph.monkey_horizontally", type=dir_map["backward"], value="PRESS", alt=True
    )
    kmi.properties.direction = "backward"
    kmi.properties.extend = False

    # Backward Extend
    kmi = km.keymap_items.new(
        "graph.monkey_horizontally",
        type=dir_map["backward"],
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "backward"
    kmi.properties.extend = True

    # TODO: ハンドル操作はPieメニューにまとめる
    # Left
    kmi = km.keymap_items.new(
        "graph.monkey_handle_selecter", type="Q", value="PRESS", alt=True
    )
    kmi.properties.handle_direction = "Left"
    kmi.properties.extend = False

    # Left Extend
    kmi = km.keymap_items.new(
        "graph.monkey_handle_selecter", type="Q", value="PRESS", alt=True, shift=True
    )
    kmi.properties.handle_direction = "Left"
    kmi.properties.extend = True

    # Right
    kmi = km.keymap_items.new(
        "graph.monkey_handle_selecter", type="E", value="PRESS", alt=True
    )
    kmi.properties.handle_direction = "Right"
    kmi.properties.extend = False

    # Right Extend
    kmi = km.keymap_items.new(
        "graph.monkey_handle_selecter", type="E", value="PRESS", alt=True, shift=True
    )
    kmi.properties.handle_direction = "Right"
    kmi.properties.extend = True

    # Focus
    kmi = km.keymap_items.new(
        "graph.view_selected_curves_range", type='F', value='PRESS')
    kmi.properties.use_frame_range = True

    # Unfocus(Builtin)
    kmi = km.keymap_items.new(
        "graph.view_all", type='F', value='PRESS', alt=True)
    # kmi.properties.include_handles = True

    addon_keymaps.append(km)


def unregister_keymaps():
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()


register, unregister = bpy.utils.register_classes_factory(
    register_keymaps, unregister_keymaps
)

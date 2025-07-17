from typing import Any
import bpy
from time import time
from ..utils.logging import get_logger

# bl_info = {
#     "name": "Hold Test",
#     "description": "Hotkey to call a menu after holding the key for a certain duration",
#     "author": "Pluglug",
#     "version": (0, 0, 1),
#     "blender": (2, 9, 0),
#     "location": "View3D > Object > Press alt+Q",
#     "warning": "It'll explode",
#     "wiki_url": "",
#     "category": "Development"
# }

log = get_logger(__name__)


class Timer:
    def __init__(self):
        self._start_time = None

    def start(self):
        if self._start_time is not None:
            raise RuntimeError("Timer is already running.")
        self._start_time = time.time()

    def elapsed(self):
        if self._start_time is None:
            raise RuntimeError("Timer has not been started.")
        return time.time() - self._start_time

    def reset(self):
        self._start_time = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed()
        self.reset()


class OBJECT_OT_call_my_menu(bpy.types.Operator):
    bl_idname = "object.call_my_menu"
    bl_label = "Call My Menu"
    bl_description = "Call a menu after holding the key for a certain duration"
    # bl_options = {'INTERNAL'}

    hold_time: bpy.props.FloatProperty(name="Hold Time", default=2.0)

    _timer: Timer = None

    def modal(self, context, event):
        if event.type == "Q" and event.value == "RELEASE":
            log.info("Key released")

            if self._timer.elapsed() >= self.hold_time:
                bpy.ops.wm.call_menu(name="OBJECT_MT_my_hold_menu")
                log.info("Menu called")
            self.cancel(context)
            log.info("Modal finished")
            # return {'FINISHED'}
            return {"CANCELLED"}

        if self._timer.elapsed() >= self.hold_time:
            log.info("Key held")
            # Do something if the key is held for the duration
            pass

        return {"RUNNING_MODAL"}

    def execute(self, context):
        log.error("This operator should be called as a modal operator")
        return {"CANCELLED"}

    def invoke(self, context, event):
        log.info("Invoke")
        self._timer = Timer()
        self._timer.start()
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._timer:
            del self._timer
            log.info("Timer deleted")


class OBJECT_MT_my_hold_menu(bpy.types.Menu):
    bl_label = "Hold menu"
    bl_idname = "OBJECT_MT_my_hold_menu"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Menu called by Hold")


class OBJECT_MT_my_menu(bpy.types.Menu):
    bl_label = "My Menu"
    bl_idname = "OBJECT_MT_my_menu"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Normal menu not caused by Hold")


classes = [
    OBJECT_OT_call_my_menu,
    OBJECT_MT_my_hold_menu,
    OBJECT_MT_my_menu,
]


addon_keymaps = []


def _keymap() -> list:
    keymap = []

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name="Object Mode", space_type="EMPTY")

    # Order is important!

    kmi = km.keymap_items.new("wm.call_menu", "Q", "PRESS", alt=True)
    kmi.properties.name = "OBJECT_MT_my_menu_normal"
    keymap.append((km, kmi))

    kmi = km.keymap_items.new("object.call_my_menu", "Q", "PRESS", alt=True)
    keymap.append((km, kmi))

    return keymap


# def register():
#     log.info("Registering Hold Test")
#     from bpy.utils import register_class
#     for cls in classes:
#         log.debug("Registering", cls.__name__)
#         register_class(cls)

#     addon_keymaps.extend(_keymap())

#     log.footer("Hold Test registered")

# def unregister():
#     log.info("Unregistering Hold Test")
#     from bpy.utils import unregister_class
#     for cls in reversed(classes):
#         log.debug("Unregistering", cls.__name__)
#         unregister_class(cls)

#     for km, kmi in addon_keymaps:
#         km.keymap_items.remove(kmi)
#     addon_keymaps.clear()

#     log.footer("Hold Test unregistered")

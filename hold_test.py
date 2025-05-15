from typing import Any
import bpy
from time import time


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
            Log.info("Key released")

            if self._timer.elapsed() >= self.hold_time:
                bpy.ops.wm.call_menu(name="OBJECT_MT_my_hold_menu")
                Log.info("Menu called")
            self.cancel(context)
            Log.footer("Modal finished")
            # return {'FINISHED'}
            return {"CANCELLED"}

        if self._timer.elapsed() >= self.hold_time:
            Log.info("Key held")
            # Do something if the key is held for the duration
            pass

        return {"RUNNING_MODAL"}

    def execute(self, context):
        Log.error("This operator should be called as a modal operator")
        return {"CANCELLED"}

    def invoke(self, context, event):
        Log.header("Invoke", "INIT")
        self._timer = Timer()
        self._timer.start()
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._timer:
            del self._timer
            Log.info("Timer deleted")


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


classes = (OBJECT_OT_call_my_menu, OBJECT_MT_my_hold_menu, OBJECT_MT_my_menu)


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
#     log.header("Registering Hold Test", "INIT")
#     from bpy.utils import register_class
#     for cls in classes:
#         log.blue("Registering", cls.__name__)
#         register_class(cls)

#     addon_keymaps.extend(_keymap())

#     log.footer("Hold Test registered")

# def unregister():
#     log.header("Unregistering Hold Test", "INIT")
#     from bpy.utils import unregister_class
#     for cls in reversed(classes):
#         log.blue("Unregistering", cls.__name__)
#         unregister_class(cls)

#     for km, kmi in addon_keymaps:
#         km.keymap_items.remove(kmi)
#     addon_keymaps.clear()

#     log.footer("Hold Test unregistered")


class Caller:

    @staticmethod
    def report_log_position(func):
        """Decorator to report the position of the caller in the log message."""

        def report_log_position(Log, *args, **kwargs):
            import traceback

            frame = traceback.extract_stack()[-2]
            module_name = frame.filename.split("\\")[-1]
            info = f"{module_name.ljust(10)} line {str(frame.lineno).ljust(4)} in {frame.name.ljust(10)}"
            func(Log, info, *args, **kwargs)

        return report_log_position

    @staticmethod
    def get_caller_info():
        """Get the file name, line number, and function name of the caller."""
        import inspect

        stack = inspect.stack()
        # 0: get_caller_info, 1: get_caller_info, 2: caller, 3: caller's caller
        if len(stack) < 3:
            return None

        frame = stack[2]
        frame_info = inspect.getframeinfo(frame[0])
        return frame_info


# Logger v2
class Log:
    """Simple Print Logger with colors."""

    class _style:
        """Style definitions for logging."""

        # Base colors can be modified
        # by adding 10 for background or 60 for bright.
        BLACK = 30
        RED = 31
        GREEN = 32
        YELLOW = 33
        BLUE = 34
        MAGENTA = 35
        CYAN = 36
        WHITE = 37

        # Styles
        RESET = 0
        BOLD = 1
        FAINT = 2
        ITALIC = 3
        UNDERLINE = 4
        INVERTED = 7

    @classmethod
    def ansi(cls, *codes: int) -> str:
        """Generates an ANSI escape code string from style codes."""
        return f'\033[{";".join(str(code) for code in codes)}m'

    LINE_LENGTH = 50
    USE_COLORS = True

    @classmethod
    def color_print(cls, color, *args):
        msg = ", ".join(str(arg) for arg in args)
        if not cls.USE_COLORS:
            print(msg)
            return
        color = [color] if not isinstance(color, (tuple, list)) else color
        print(f"{cls.ansi(*color)}{msg}{cls.ansi(cls._style.RESET)}")

    @classmethod
    def info(cls, *args):
        cls.color_print(cls._style.BLUE, *args)

    @classmethod
    def warn(cls, *args):
        cls.color_print(cls._style.YELLOW, *args)

    @classmethod
    def error(cls, *args):
        cls.color_print(cls._style.RED, *args)

    # --- Additional methods ---

    @classmethod
    def header(cls, *args, title=None):
        print("")
        title_line, msg = cls._gen_section(*args, title=title)
        cls.color_print(
            (cls._style.GREEN, cls._style.BOLD),
            title_line + (f"\n{msg}" if args else ""),
        )

    @classmethod
    def footer(cls, *args, title=None):
        title_line, msg = cls._gen_section(*args, title=title)
        cls.color_print(cls._style.CYAN, (f"{msg}\n" if args else "") + title_line)
        print("")

    @classmethod
    def _gen_section(cls, *args, title=None):
        msg = ", ".join(str(arg) for arg in args).strip()
        section_length = cls.LINE_LENGTH if not args else max(len(msg), cls.LINE_LENGTH)
        title_line = (
            title.center(section_length, "-")
            if title is not None
            else "-" * section_length
        )
        return title_line, msg


class DebugTimer:
    def __init__(self):
        self._start_time = None
        self._lap_times = []

    def print_time(self, *args):
        color = (Log._style.WHITE + 10, Log._style.BOLD)  # White background
        Log.color_print(color, *args)

    def start(self, msg=None, title=None):
        if self._start_time is not None:
            raise RuntimeError("Timer is already running.")
        self._start_time = time()
        Log.header(msg, title)

    def elapsed(self):
        if self._start_time is None:
            raise RuntimeError("Timer has not been started.")
        return time() - self._start_time

    def reset(self):
        self._start_time = None
        self._lap_times.clear()

    def lap(self, label=None):
        if self._start_time is None:
            raise RuntimeError("Timer has not been started.")
        lap_time = time() - self._start_time
        self._lap_times.append((label, lap_time))

        self.print_time(
            f"- Lap {len(self._lap_times)}: {label if label else 'No label'} - {lap_time:.4f} "
        )
        return lap_time

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._start_time is not None:
            elapsed = self.elapsed()
            self.print_time(f"Elapsed time: {elapsed:.4f} sec")
            self.reset()

        if exc_type is not None:
            Log.error(
                f"An exception occurred: {exc_value}\n{Log.ansi(Log._style.CYAN)}{traceback}"
            )
            return False
        return True

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    @property
    def lap_times(self):
        """Can be used to find sums, averages, minimum maximum values, etc."""
        return self._lap_times

    @property
    def total_time(self):
        return sum(t for _, t in self._lap_times)


debug_timer = DebugTimer()


if __name__ == "__main__":
    # Log Test
    Log.header("Log Test", title="INIT")
    Log.info("Info message")

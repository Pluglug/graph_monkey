from enum import Enum
import contextlib
import traceback
import inspect
import time
import os


# Create global debug flags for the project
# Must have "DBG" prefix
DBG = True
DBG_INIT = True
DBG_OPS = True
DBG_PREFS = True
DBG_OVLY = True


class Color(Enum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97
    # Add 10 if using background colors
    # ansi(Color.WHITE + 10)


class Style(Enum):
    RESET = 0
    BOLD = 1
    FAINT = 2
    ITALIC = 3
    UNDERLINE = 4
    INVERTED = 7


def ansi(*styles: Enum) -> str:
    """
    Generate ANSI escape code for given styles.
    :param styles: Enum(int) values from Color or Style
    :return: String containing ANSI escape code
    """
    return "\033[{}m".format(";".join(str(color.value) for color in styles))


class PrintLog:
    def __init__(self):
        self.indent_level = 0
        self.track_caller_location = False
        self.use_colors = True
        self.timer = None
        self.line_length = 50

    def _get_caller_location(self):
        if not self.track_caller_location:
            return ""

        frame = traceback.extract_stack(None, 4)[0]  # Get caller's frame
        module_name = frame.filename.split("\\")[-1]
        return f"{module_name.ljust(10)}: {str(frame.lineno).ljust(4)} {frame.name.ljust(10)}: "

    def _log(self, color, *args):
        caller_info = self._get_caller_location()
        indent = "  " * self.indent_level
        msg = caller_info + indent + ", ".join(str(arg) for arg in args)
        msg = msg.replace("\n", "\n" + indent)

        if self.use_colors:
            print(color + msg + ansi(Style.RESET))
        else:
            print(msg)

    def header(self, msg=None, title=None):
        """Green text indicating the start of a new operation."""
        print("")
        if title is not None:
            title = str(title)
            header_length = max(len(msg), self.line_length)  # len(title)+8)
            title_text = title.center(header_length, "-")
        else:
            title_text = "-" * self.line_length
        self._log(ansi(Color.GREEN, Style.BOLD), title_text)
        if msg:
            self._log(ansi(Color.GREEN, Style.BOLD), msg)
        return self

    def footer(self, *args):
        """Green text indicating the end of an operation."""
        self.reset_indent()
        footer_text = ", ".join(str(arg) for arg in args)
        self._log(ansi(Color.CYAN), footer_text + "\n" + "-" * self.line_length)
        print("")
        return self

    def info(self, *args):
        """Blue text indicating the progress of an operation."""
        self._log(ansi(Color.BLUE), *args)
        return self

    def info2(self, *args):
        """Cyan text indicating the progress of an operation."""
        self._log(ansi(Color.CYAN), *args)
        return self

    def error(self, *args):
        """Red text indicating an error that is not fatal."""
        self._log(ansi(Color.RED), *args)
        return self

    def warn(self, *args):
        """Yellow text indicating a warning that is not fatal."""
        self._log(ansi(Color.YELLOW), *args)
        return self

    warning = warn

    def __call__(self, *args):
        """Display the arguments in blue."""
        self.info(*args)
        return self

    @staticmethod
    def get_caller_info():
        stack = inspect.stack()

        # 0: get_caller_info, 1: log.get_caller_info, 2: caller
        if len(stack) < 3:
            return "Unknown caller"

        frame = stack[2]
        frame_info = inspect.getframeinfo(frame[0])

        return frame_info
        # return {
        #     "filename": os.path.basename(frame_info.filename),
        #     "lineno": frame_info.lineno,
        #     "function": frame_info.function,
        #     # "code_context": frame_info.code_context
        # }

    # あんまり便利じゃない
    # `log(" " * len(path) + "/".join(path))`とかのほうがシンプルでよい
    # デコレーターとして使えるなら便利かも
    @contextlib.contextmanager
    def indented(self):
        # caller_function = inspect.stack()[2].function
        self.increase()
        # self.header(f"Start {caller_function}")
        try:
            yield
        finally:
            # self._log(CONSOLE_COLOR_CYAN, f"End {caller_function}")
            self.decrease()

    def indent(self, count=1):
        """Increase the indent level."""
        self.indent_level = max(0, self.indent_level + count)
        return self

    def increase(self, count=1):
        """Increase the indent level."""
        self.indent_level = max(0, self.indent_level + count)
        return self

    def decrease(self, count=1):
        """Decrease the indent level."""
        self.indent_level = max(0, self.indent_level - count)
        return self

    def reset_indent(self):
        """Reset the indent level to zero."""
        self.indent_level = 0
        return self

    class Stopwatch:
        def __init__(self, log):
            self.log = log
            self.timer = None
            self._lap_times = []

        def start(self, msg, title=None):
            """Stopwatch start and call header()"""
            self.log.header("Stopwatch started: " + msg, title)
            self.timer = time.time()

        def elapsed(self, *args):
            """Display the elapsed time since the stopwatch was started."""
            if self.timer is None:
                self.log.warn("Stopwatch is not started.")
                return

            elapsed = time.time() - self.timer
            self.log._log(ansi(Color.GREEN), f"Elapsed time: {elapsed:.4f} sec", *args)

        def lap(self, label=None):
            if self.timer is None:
                self.log.warn("Stopwatch is not started.")
                return

            elapsed_time = self.elapsed()
            self._lap_times.append((label, elapsed_time))
            return elapsed_time

        def reset(self):
            self.timer = None
            self._lap_times.clear()

        def stop(self, msg="Stopwatch stopped.", *args):
            """Stop the stopwatch and display the total elapsed time."""
            if self.timer is not None:
                self.elapsed(msg, *args)
                self.timer = None
            else:
                self.log.warn("Stopwatch is not started.")

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            elapsed_time = self.elapsed()
            self.stop()
            return elapsed_time

        def __call__(self, func):
            def wrapper(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)

            return wrapper

        @property
        def lap_times(self):
            return self._lap_times

        @property
        def total_time(self):
            return sum(t for _, t in self._lap_times)

        @property
        def average_time(self):
            if not self._lap_times:
                return 0
            return self.total_time / len(self._lap_times)

        @property
        def min_time(self):
            return min(t for _, t in self._lap_times) if self._lap_times else 0

        @property
        def max_time(self):
            return max(t for _, t in self._lap_times) if self._lap_times else 0

    def stopwatch(self):
        return self.Stopwatch(self)


log = PrintLog()

# Usage:
# from debug import log, DBG_HOGE
# DBG_HOGE and log.header("Start processing...").increase()
# for item in data_list:
#     DBG_HOGE and log.info("Processing item:", item, "Status:", process_status)


import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty


def _collect_debug_flags():
    """Collect all DBG* flags and add them to a list."""
    return [name for name in globals() if name.startswith("DBG")]


# def _create_debug_properties_group():
#     debug_flags = _collect_debug_flags()

#     class DebugFlagsGroup(PropertyGroup):
#         pass

#     # Add a bool property to the class for each debug flag
#     for flag in debug_flags:
#         setattr(DebugFlagsGroup, flag, BoolProperty(name=flag, default=globals()[flag]))

#     return DebugFlagsGroup


class DebugFlagsGroup(PropertyGroup):
    developer_mode: BoolProperty(name="Developer Mode", default=False)

    @classmethod
    def _create_debug_properties(cls):
        """Dynamically add debug flags as BoolProperties to the DebugFlagsGroup."""
        for name in globals():
            if name.startswith("DBG"):
                setattr(
                    cls,
                    name,
                    BoolProperty(
                        name=name,
                        default=globals()[name],
                        update=cls._generate_update_function(name),
                    ),
                )
                DBG_INIT and log.info("Added debug flag:", name)

    @staticmethod
    def _generate_update_function(
        name,
    ):  # 無理っぽい Sceneへフラグを追加しなければならない
        def update(self, context):
            globals()[name] = getattr(self, name)

        return update

    def draw(self, context, layout):
        """Draw the UI elements for the debug flags."""
        layout.prop(
            self, "developer_mode", text="Developer Mode", toggle=True, icon="SCRIPT"
        )

        if self.developer_mode:
            box = layout.box()
            self._draw_debug_flags(box)

    def _draw_debug_flags(self, layout):
        col = layout.column(heading="Debug Flags:")
        col.use_property_split = True
        col.use_property_decorate = False

        for name in globals():
            if name.startswith("DBG"):
                col.prop(self, name)


# def register():
#     bpy.utils.register_class(DebugFlagsGroup)
#     DebugFlagsGroup._create_debug_properties()

#     bpy.types.Scene.debug_flags = bpy.props.PointerProperty(type=DebugFlagsGroup)


__all__ = ["log"]
__all__ += _collect_debug_flags()
__all__ += ["DebugFlagsGroup"]


if __name__ == "__main__":
    pass

from typing import Dict
import time

import bpy

from ..addon import ADDON_PREFIX, ADDON_PREFIX_PY


class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.reset(duration)

    def update(self):
        current_time = time()
        elapsed_time = current_time - self.start_time
        self.remaining_time -= elapsed_time
        self.start_time = current_time

        return self.remaining_time <= 0

    def reset(self, duration):
        self.duration = duration
        self.remaining_time = duration
        self.start_time = time()

    # def remaining_percentage(self):
    #     # Transitions from 100 to 0
    #     return max(0, self.remaining_time / self.duration * 100)

    def elapsed_ratio(self):
        """Returns the ratio of elapsed time to total duration."""
        return max(0, min(1, (self.duration - self.remaining_time) / self.duration))

    def is_finished(self):
        return self.remaining_time <= 0


class Timeout:
    """
    遅延実行用オペレータ

    Blenderのイベントシステムを利用して、指定された関数を
    一定時間後に実行します。UIスレッドのブロックを回避する
    ために使用します。
    """

    bl_idname = f"{ADDON_PREFIX_PY}.timeout"
    bl_label = ""
    bl_options = {"INTERNAL"}

    idx: bpy.props.IntProperty(options={"SKIP_SAVE", "HIDDEN"})
    delay: bpy.props.FloatProperty(default=0.0001, options={"SKIP_SAVE", "HIDDEN"})

    _data: Dict[int, tuple] = dict()  # タイムアウト関数のデータ保持用
    _timer = None
    _finished = False

    def modal(self, context, event):
        if event.type == "TIMER":
            if self._finished:
                context.window_manager.event_timer_remove(self._timer)
                del self._data[self.idx]
                return {"FINISHED"}

            if self._timer.time_duration >= self.delay:
                self._finished = True
                try:
                    func, args = self._data[self.idx]
                    func(*args)
                except Exception as e:
                    print(f"Timeout error: {str(e)}")
        return {"PASS_THROUGH"}

    def execute(self, context):
        self._finished = False
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(
            self.delay, window=context.window
        )
        return {"RUNNING_MODAL"}


TimeoutOperator = type(
    "%s_OT_timeout" % ADDON_PREFIX, (Timeout, bpy.types.Operator), {}
)


def timeout(func: callable, *args) -> None:
    """
    関数を遅延実行

    Blenderのモーダルイベントを利用して関数を非同期で実行します。
    UI更新や時間のかかる処理の分散に役立ちます。

    Args:
        func: 実行する関数
        *args: 関数に渡す引数
    """
    idx = len(Timeout._data)
    while idx in Timeout._data:
        idx += 1
    Timeout._data[idx] = (func, args)
    getattr(bpy.ops, ADDON_PREFIX_PY).timeout(idx=idx)

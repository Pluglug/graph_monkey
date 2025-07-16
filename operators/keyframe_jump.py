import bpy
from bpy.types import Operator, Context, Area
from bpy.props import BoolProperty

from ..utils.logging import get_logger
from ..keymap.keymap_manager import KeymapDefinition, keymap_registry

log = get_logger(__name__)


class MONKEY_OT_JUMP_WITHIN_RANGE(Operator):
    bl_idname = "keyframe.jump_within_range"
    bl_label = "Jump within range"
    bl_description = "Jump within range"
    bl_options = set()

    next: BoolProperty(default=True, options={"SKIP_SAVE"})
    loop: BoolProperty(default=True, options={"SKIP_SAVE"})

    def execute(self, context: Context):
        scene = context.scene

        if scene.use_preview_range:
            self.start_frame = scene.frame_preview_start
            self.end_frame = scene.frame_preview_end
        else:
            self.start_frame = scene.frame_start
            self.end_frame = scene.frame_end

        timeline_area = self.find_area_with_visible_fcurves(context)
        if timeline_area:
            with context.temp_override(area=timeline_area):
                return self.jump_within_range(context)
        else:
            # タイムラインエリアがない場合は通常ジャンプ
            self.report({"INFO"}, "No Timeline area found")
            bpy.ops.screen.keyframe_jump(next=self.next)
            return {"FINISHED"}

    @staticmethod
    def find_area_with_visible_fcurves(context: Context) -> Area | None:
        """
        context.window.screen.areas から visible_fcurves を持つエリアを探して返す。
        見つからなければ None。
        """
        for area in context.window.screen.areas:
            with context.temp_override(area=area):
                if hasattr(context, "visible_fcurves"):
                    return area
        return None

    @staticmethod
    def visible_key_on_current_frame(context: Context) -> bool:
        """
        contextとタイムラインエリアを受け取り、
        現在のフレーム位置に可視状態のキーフレームがあればTrue、なければFalseを返す
        """
        scene = context.scene
        current_frame = scene.frame_current

        visible_fcurves = (
            context.visible_fcurves if hasattr(context, "visible_fcurves") else []
        )
        for fcurve in visible_fcurves:
            for kp in fcurve.keyframe_points:
                if int(kp.co.x) == current_frame:
                    return True
        return False

    def jump_within_range(self, context: Context):
        scene = context.scene
        current_frame = scene.frame_current

        bpy.ops.screen.keyframe_jump(next=self.next)
        new_frame = scene.frame_current

        out_of_range = new_frame < self.start_frame or new_frame > self.end_frame
        did_not_move = new_frame == current_frame

        if (did_not_move or out_of_range) and self.loop:
            # 逆端に移動
            if self.next:
                scene.frame_set(self.start_frame)
            else:
                scene.frame_set(self.end_frame)

            # 逆端に可視キーフレームがあれば終了
            if self.visible_key_on_current_frame(context):
                return {"FINISHED"}

            # なければもう一度ジャンプ
            bpy.ops.screen.keyframe_jump(next=self.next)
        return {"FINISHED"}


class MONKEY_OT_KEYFRAME_PEEK(Operator):
    bl_idname = "keyframe.peek_next"
    bl_label = "Peek Next Keyframe"
    bl_description = (
        "Peek next/previous keyframe while key is held down, return to original frame when released. "
        "Ctrl key to stay at the destination frame. "
    )

    next: BoolProperty(default=True, options={"SKIP_SAVE"})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_frame = None
        self.peek_key_type = None

    def modal(self, context, event):
        # 押されたキーと同じキーが離されたかを判定
        if event.type == self.peek_key_type and event.value == "RELEASE":
            # Ctrlキーが押されている場合は、現在のフレームにとどまって終了
            if event.ctrl:
                # 移動先にとどまる（original_frameには戻らない）
                self.original_frame = None
                return {"FINISHED"}

            # 通常の場合は元のフレームに戻る
            if self.original_frame is not None:
                context.scene.frame_set(self.original_frame)
                self.original_frame = None
            return {"FINISHED"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        # キータイプを設定
        self.peek_key_type = event.type

        # 元のフレームを記憶
        self.original_frame = context.scene.frame_current

        # タイムラインエリアを探す
        timeline_area = MONKEY_OT_JUMP_WITHIN_RANGE.find_area_with_visible_fcurves(
            context
        )

        if timeline_area:
            with context.temp_override(area=timeline_area):
                # 次のキーフレームへジャンプ
                bpy.ops.screen.keyframe_jump(next=self.next)
        else:
            # タイムラインエリアがない場合は通常ジャンプ
            bpy.ops.screen.keyframe_jump(next=self.next)

        # モーダル開始
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


KEYFRAME_JUMP_KEYMAPS = [
    ("Dopesheet", "DOPESHEET_EDITOR"),
    ("Frames", "EMPTY"),
    ("Graph Editor", "GRAPH_EDITOR"),
    ("Object Mode", "EMPTY"),
    ("Pose", "EMPTY"),
]

keymap_definitions = []

for keymap_name, keymap_space_type in KEYFRAME_JUMP_KEYMAPS:
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="screen.frame_offset",  # Built-in operator
            key="ONE",
            value="PRESS",
            repeat=True,
            properties={"delta": -1},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="screen.frame_offset",  # Built-in operator
            key="TWO",
            value="PRESS",
            repeat=True,
            properties={"delta": 1},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.jump_within_range",
            key="THREE",
            value="PRESS",
            repeat=True,
            properties={"next": False, "loop": True},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.jump_within_range",
            key="FOUR",
            value="PRESS",
            repeat=True,
            properties={"next": True, "loop": True},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.peek_next",
            key="THREE",
            shift=True,
            value="PRESS",
            repeat=False,
            properties={"next": False},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )
    keymap_definitions.append(
        KeymapDefinition(
            operator_id="keyframe.peek_next",
            key="FOUR",
            shift=True,
            value="PRESS",
            repeat=False,
            properties={"next": True},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )

keymap_registry.register_keymap_group("Keyframe Jump", keymap_definitions)


# def register():
#     bpy.types.Scene.keyframe_jump_wrap = BoolProperty(
#         name="Loop Keyframe Jump",
#         description="Loop keyframe jump within frame range",
#         default=True,
#     )
# def unregister():
#     del bpy.types.Scene.keyframe_jump_wrap

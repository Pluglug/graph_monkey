import bpy
from bpy.types import Operator, Context, Area
from bpy.props import BoolProperty, StringProperty

from ..utils.logging import get_logger
from ..keymap.keymap_manager import KeymapDefinition, keymap_registry

log = get_logger(__name__)


def jump_or_wrap(next=True):
    current_frame = bpy.context.scene.frame_current

    bpy.ops.screen.keyframe_jump(next=next)

    if bpy.context.scene.frame_current == current_frame:
        # キーフレームが存在しない場合の処理
        if next:
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        else:
            bpy.context.scene.frame_set(bpy.context.scene.frame_end)


class MONKEY_OT_JUMP_WITHIN_RANGE(Operator):
    bl_idname = "keyframe.jump_within_range"
    bl_label = "Jump within range"
    bl_description = "Jump within range"
    bl_options = set()

    next: BoolProperty(default=True, options={"SKIP_SAVE"})
    loop: BoolProperty(default=True, options={"SKIP_SAVE"})
    called_from: StringProperty(default="", options={"SKIP_SAVE"})

    def execute(self, context: Context):
        log.debug(f"Keymap: {self.called_from}")
        scene = context.scene

        if scene.use_preview_range:
            self.start_frame = scene.frame_preview_start
            self.end_frame = scene.frame_preview_end
        else:
            self.start_frame = scene.frame_start
            self.end_frame = scene.frame_end

        # 直接jump_within_rangeを実行
        # TIMELINE切り替えはvisible_fcurvesが必要な時のみ行う
        return self.jump_within_range(context)

    @staticmethod
    def find_timeline_area(context: Context) -> Area | None:
        for area in context.window.screen.areas:
            if area.ui_type == "TIMELINE":
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

        # visible_fcurvesが存在し、かつNoneでないことを確認
        visible_fcurves = getattr(context, "visible_fcurves", None)
        if not visible_fcurves:
            return False

        for fcurve in visible_fcurves:
            for kp in fcurve.keyframe_points:
                if int(kp.co.x) == current_frame:
                    return True
        return False

    def screen_keyframe_jump_with_fallback(self, context: Context) -> bool:
        """When outside of timeline area, keyframe_jump fails.
        Fallback to frame_offset.
        """
        try:
            bpy.ops.screen.keyframe_jump(next=self.next)
            return True
        except RuntimeError as e:
            log.error(f"keyframe_jump failed in {context.area.ui_type}: {e}")
            if self.next:
                bpy.ops.screen.frame_offset(delta=1)
            else:
                bpy.ops.screen.frame_offset(delta=-1)
            return False

    def jump_within_range(self, context: Context):
        scene = context.scene
        current_frame = scene.frame_current

        if not self.screen_keyframe_jump_with_fallback(context):
            return {"FINISHED"}

        new_frame = scene.frame_current

        out_of_range = new_frame < self.start_frame or new_frame > self.end_frame
        did_not_move = new_frame == current_frame

        if (did_not_move or out_of_range) and self.loop:
            # 逆端に移動
            if self.next:
                scene.frame_set(self.start_frame)
            else:
                scene.frame_set(self.end_frame)

            # 逆端に可視キーフレームがあれば終了（TIMELINE context override付き）
            if self.visible_key_on_current_frame_with_timeline_fallback(context):
                return {"FINISHED"}

            # なければもう一度ジャンプ
            self.screen_keyframe_jump_with_fallback(context)
        return {"FINISHED"}

    def visible_key_on_current_frame_with_timeline_fallback(self, context: Context) -> bool:
        """
        visible_key_on_current_frameをTIMELINEコンテキストで実行
        TIMELINEエリアがない場合はFalseを返す
        """
        # まず現在のコンテキストで試す
        if hasattr(context, "visible_fcurves") and context.visible_fcurves:
            return self.visible_key_on_current_frame(context)
        
        # TIMELINEエリアを探して一時的に切り替え
        timeline_area = self.find_timeline_area(context)
        if timeline_area:
            with context.temp_override(area=timeline_area):
                return self.visible_key_on_current_frame(context)
        
        # TIMELINEエリアがない場合は、他のアニメーションエリアを試す
        animation_areas = ["DOPESHEET_EDITOR", "GRAPH_EDITOR", "NLA_EDITOR"]
        for area_type in animation_areas:
            for area in context.window.screen.areas:
                if area.type == area_type:
                    with context.temp_override(area=area):
                        if hasattr(context, "visible_fcurves") and context.visible_fcurves:
                            return self.visible_key_on_current_frame(context)
        
        return False


# TODO: Prefsで定義する
# def register():
#     bpy.types.Scene.keyframe_jump_wrap = BoolProperty(
#         name="Loop Keyframe Jump",
#         description="Loop keyframe jump within frame range",
#         default=True,
#     )


# def unregister():
#     del bpy.types.Scene.keyframe_jump_wrap

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
            properties={"next": False, "loop": True, "called_from": keymap_name},
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
            properties={"next": True, "loop": True, "called_from": keymap_name},
            name=keymap_name,
            space_type=keymap_space_type,
        )
    )

keymap_registry.register_keymap_group("Keyframe Jump", keymap_definitions)

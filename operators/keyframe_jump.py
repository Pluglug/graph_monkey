import bpy
from bpy.types import Operator, BoolProperty

from ..utils.logging import get_logger

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


def jump_within_range(next=True):
    scene = bpy.context.scene
    current_frame = scene.frame_current
    start_frame = scene.frame_start
    end_frame = scene.frame_end

    bpy.ops.screen.keyframe_jump(next=next)
    new_frame = scene.frame_current

    loop = bpy.context.scene.keyframe_jump_wrap

    if bpy.context.scene.frame_current == current_frame and loop:
        # キーフレームが存在しない場合の処理
        if next:
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        else:
            bpy.context.scene.frame_set(bpy.context.scene.frame_end)  # 使い勝手が悪い

    # ジャンプ後のフレームが再生範囲外の場合は範囲内に戻す
    if new_frame < start_frame or new_frame > end_frame:
        if next:
            scene.frame_set(start_frame)
        else:
            scene.frame_set(end_frame)


# def register():
#     bpy.types.Scene.keyframe_jump_wrap = BoolProperty(
#         name="Loop Keyframe Jump",
#         description="Loop keyframe jump within frame range",
#         default=True,
#     )


# def unregister():
#     del bpy.types.Scene.keyframe_jump_wrap

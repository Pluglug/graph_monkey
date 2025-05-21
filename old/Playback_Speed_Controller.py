bl_info = {
    "name": "Playback Speed Controller",
    "blender": (2, 80, 0),
    "category": "Animation",
    "version": (1, 0, 0),
    "author": "Pluglug",
    "description": "Control the playback speed of the animation",
}


import bpy
import bpy.app.handlers as handlers
from bpy.props import FloatProperty, EnumProperty
from bpy.types import Scene, Operator, Panel


preset_items = [
    ("0.25", "0.25x", ""),
    ("0.5", "0.5x", ""),
    ("1.0", "1.0x", ""),
    ("1.5", "1.5x", ""),
    ("2.0", "2.0x", ""),
    ("4.0", "4.0x", ""),
]


class PlaybackController:
    def __init__(self, scene):
        self.scene = scene

    def store_original_range(self):
        self.scene["original_start"] = self.scene.frame_start
        self.scene["original_end"] = self.scene.frame_end

    def adjust_range(self, frame_map_old, frame_map_new):
        ratio = frame_map_new / frame_map_old
        new_start = round(self.scene["original_start"] * ratio)
        new_end = round(self.scene["original_end"] * ratio)

        self.scene.frame_start = new_start
        self.scene.frame_end = new_end

    def apply_speed(self, playback_speed):
        playback_speed = round(playback_speed, 2)
        frame_map_old = round(playback_speed * 100)
        frame_map_old = max(1, min(900, frame_map_old))

        self.scene.render.frame_map_old = frame_map_old
        self.scene.render.frame_map_new = 100

        self.adjust_range(frame_map_old, self.scene.render.frame_map_new)


class SCENE_OT_store_original_range(Operator):
    bl_idname = "scene.store_original_range"
    bl_label = "Store Original Playback Range"
    bl_description = "Store the original playback range before applying playback speed adjustments"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        controller = PlaybackController(context.scene)
        controller.store_original_range()
        return {'FINISHED'}


class SCENE_OT_reset_speed(Operator):
    bl_idname = "scene.reset_speed"
    bl_label = "Reset Playback Speed"
    bl_description = "Reset playback speed and return to original playback range"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        controller = PlaybackController(context.scene)
        controller.adjust_range(100, 100)
        context.scene.playback_speed = 1.0
        controller.apply_speed(1.0)
        return {'FINISHED'}


def on_speed_update(scene, context):
    if not scene.get("updating_preset"):
        controller = PlaybackController(scene)
        controller.apply_speed(scene.playback_speed)
        closest_preset = find_closest_preset(scene.playback_speed)
        scene["updating_preset"] = True
        scene.playback_speed_preset = closest_preset
        scene["updating_preset"] = False


def on_preset_update(scene, context):
    if not scene.get("updating_speed"):
        scene["updating_speed"] = True
        scene.playback_speed = float(scene.playback_speed_preset)
        on_speed_update(scene, context)
        scene["updating_speed"] = False


def find_closest_preset(value):
    closest_preset = None
    smallest_difference = float('inf')

    for preset_value, _, _ in preset_items:
        difference = abs(float(preset_value) - value)
        if difference < smallest_difference:
            smallest_difference = difference
            closest_preset = preset_value

    return closest_preset


Scene.playback_speed = FloatProperty(
    name="Playback Speed",
    description="Control the playback speed of the animation",
    default=1.0,
    min=0.01,
    max=9.0,
    soft_min=0.1,
    soft_max=2.0,
    step=10,
    precision=2,
    update=on_speed_update,
    subtype='FACTOR'
)

Scene.playback_speed_preset = EnumProperty(
    name="Playback Speed Preset",
    description="Select a playback speed preset",
    items=preset_items,
    default="1.0",
    update=on_preset_update
)


def draw_ui(self, context):
    layout = self.layout
    scene = context.scene

    layout.prop(scene, "playback_speed", text="", icon='MOD_TIME')
    # layout.prop(scene, "playback_speed_preset", text="")

    if (scene.get("original_start") is not None and
            (scene["original_start"] != scene.frame_start or scene["original_end"] != scene.frame_end)):
        store_icon = 'SEQUENCE_COLOR_01'
    else:
        store_icon = 'SEQUENCE_COLOR_04'

    layout.operator("scene.store_original_range", text="", icon=store_icon)

    if scene.playback_speed != 1.00:
        reset_icon = 'CANCEL'
    else:
        reset_icon = 'PLAY'

    layout.operator("scene.reset_speed", text="", icon=reset_icon)


def store_range_on_load(dummy):
    controller = PlaybackController(bpy.context.scene)
    controller.store_original_range()
    controller.apply_speed(bpy.context.scene.playback_speed)


def register():
    bpy.utils.register_class(SCENE_OT_reset_speed)
    bpy.utils.register_class(SCENE_OT_store_original_range)
    bpy.types.DOPESHEET_HT_header.append(draw_ui)
    handlers.load_post.append(store_range_on_load)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_reset_speed)
    bpy.utils.unregister_class(SCENE_OT_store_original_range)
    bpy.types.DOPESHEET_HT_header.remove(draw_ui)
    handlers.load_post.remove(store_range_on_load)


if __name__ == "__main__":
    register()
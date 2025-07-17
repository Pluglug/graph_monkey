# bl_info = {
#     "name": "MonKey",
#     "author": "Pluglug",
#     "version": (0, 6, 5),
#     "blender": (2, 80, 0),
#     "location": "Graph Editor",
#     "description": "Move keyframe selection in the Graph Editor",
#     "warning": "",
#     "wiki_url": "",
#     "category": "Animation",
# }
# pyright: reportInvalidTypeForm=false

import bpy
import blf
import re
import time

from mathutils import Vector
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
)


class GRAPH_OT_monkey_horizontally(bpy.types.Operator):
    bl_idname = "graph.monkey_horizontally"
    bl_label = "MonKey for Horizontal"
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[("forward", "Forward", ""), ("backward", "Backward", "")],
        default="forward",
    )
    extend: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        if context.area.type != "GRAPH_EDITOR":
            return False

        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        return bool(visible_objects)

    def execute(self, context):
        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        move_keyframe_selection_horizontally(
            self.direction, self.extend, visible_objects
        )
        return {"FINISHED"}


class GRAPH_OT_monkey_vertically(bpy.types.Operator):
    bl_idname = "graph.monkey_vertically"
    bl_label = "MonKey for Vertical"
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        name="Direction",
        description="Direction to move the selected channels",
        items=[
            ("upward", "Upward", "Move the selected channels upward"),
            ("downward", "Downward", "Move the selected channels downward"),
        ],
        default="downward",
    )
    extend: bpy.props.BoolProperty(
        name="Extend",
        description="Extend the channel selection instead of moving",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        if context.area.type != "GRAPH_EDITOR":
            return False

        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        return bool(visible_objects)

    def execute(self, context):
        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        move_channel_selection_vertically(self.direction, self.extend, visible_objects)

        # Get channel information
        # display_props = context.scene.monkey_display_properties
        channel_info = get_channel_info(visible_objects)  # , display_props)
        if channel_info:
            print(channel_info)
            print()

            # Draw text overlay using display properties
            region = context.region
            width = region.width / 2 + display_props.text_position_x
            bpy.ops.graph.draw_text(
                text=channel_info,
                coords=(width, display_props.text_position_y),
                center=True,
                color=display_props.text_color,
                time=display_props.display_time,
                alpha=0.5,
            )

        return {"FINISHED"}


class GRAPH_OT_draw_text(bpy.types.Operator):
    bl_idname = "graph.draw_text"
    bl_label = "Draw Text"
    bl_description = "Draw text overlay in the Graph Editor"
    bl_options = {"INTERNAL"}

    text: StringProperty(name="Text to draw", default="Text")
    coords: FloatVectorProperty(name="Screen Coordinates", size=2, default=(100, 100))
    center: BoolProperty(name="Center", default=True)
    color: FloatVectorProperty(name="Color", size=3, default=(1, 1, 1))

    time: FloatProperty(name="", default=2, min=0.1)
    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)

    def draw_text_overlay(self, context):
        display_props = context.scene.monkey_display_properties
        alpha = self.countdown / self.time * self.alpha
        draw_text(
            context,
            self.text,
            self.coords,
            self.center,
            self.color,
            alpha,
            fontsize=display_props.font_size,
        )

    def modal(self, context, event):
        context.area.tag_redraw()

        if self.countdown < 0:
            # Remove event timer and draw handler before returning 'FINISHED'
            context.window_manager.event_timer_remove(self.TIMER)
            bpy.types.SpaceGraphEditor.draw_handler_remove(self.HUD, "WINDOW")
            return {"FINISHED"}

        if event.type == "TIMER":
            self.countdown -= 0.1

        return {"PASS_THROUGH"}

    def execute(self, context):
        self.HUD = bpy.types.SpaceGraphEditor.draw_handler_add(
            self.draw_text_overlay, (context,), "WINDOW", "POST_PIXEL"
        )
        self.TIMER = context.window_manager.event_timer_add(0.1, window=context.window)
        self.countdown = self.time

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


def draw_text(
    context, text, coords=None, center=True, color=(1, 1, 1), alpha=1, fontsize=32
):
    if not coords:
        region = context.region
        width = region.width / 2
        height = region.height / 2
    else:
        width, height = coords

    font = 0

    blf.size(font, fontsize)
    blf.color(font, *color, alpha)

    if center:
        blf.position(
            font,
            width - (int(len(text) * fontsize * 0.4) / 2),
            height + int(fontsize),
            0,
        )
    else:
        blf.position(font, *(coords), 1)

    blf.draw(font, text)


class MonKeyDisplayProperties(bpy.types.PropertyGroup):
    show_object_name: bpy.props.BoolProperty(
        name="Show Object Name",
        description="Display the object name in the output",
        default=False,
    )

    show_action_name: bpy.props.BoolProperty(
        name="Show Action Name",
        description="Display the action name in the output",
        default=False,
    )

    show_group_name: bpy.props.BoolProperty(
        name="Show Group Name",
        description="Display the group name in the output",
        default=True,
    )

    show_channel_name: bpy.props.BoolProperty(
        name="Show Channel Name",
        description="Display the channel name in the output",
        default=True,
    )

    font_size: bpy.props.IntProperty(
        name="Font Size",
        description="Size of the text overlay font",
        default=32,
        min=6,
        soft_max=48,
    )

    text_color: bpy.props.FloatVectorProperty(
        name="Text Color",
        description="Color of the text overlay",
        size=3,
        default=(1, 1, 1),
        subtype="COLOR",
        min=0,
        max=1,
    )

    text_position_x: bpy.props.IntProperty(
        name="Text Position X",
        description="Horizontal position of the text overlay",
        default=0,
        min=0,
        soft_max=500,
    )

    text_position_y: bpy.props.IntProperty(
        name="Text Position Y",
        description="Vertical position of the text overlay",
        default=40,
        min=0,
        soft_max=500,
    )

    display_time: bpy.props.FloatProperty(
        name="Display Time",
        description="Duration for which the text overlay is displayed",
        default=3.0,
        min=0.1,
        soft_max=10.0,
    )


bpy.utils.register_class(MonKeyDisplayProperties)
# Add the property group to the Scene type
bpy.types.Scene.monkey_display_properties = bpy.props.PointerProperty(
    type=MonKeyDisplayProperties
)


def convert_data_path_to_readable(channel_data_path):
    readable_data_path = (
        channel_data_path.replace('["', " ").replace('"].', " < ").replace("_", " ")
    )
    readable_data_path = re.sub(r"(\.)([A-Z])", r"\1 \2", readable_data_path)
    readable_data_path = " ".join(
        word.capitalize() for word in readable_data_path.split(" ")
    )
    return readable_data_path


def get_channel_info(visible_objects, display_props):
    selected_channels = [
        (obj, fcurve)
        for obj in visible_objects
        for fcurve in obj.animation_data.action.fcurves
        if fcurve.select
    ]

    if len(selected_channels) == 1:
        obj, fcurve = selected_channels[0]  # Unpack the tuple
        object_name = obj.name if display_props.show_object_name else None
        action_name = fcurve.id_data.name if display_props.show_action_name else None
        group_name = (
            fcurve.group.name
            if fcurve.group and display_props.show_group_name
            else None
        )
        channel_name = (
            convert_data_path_to_readable(fcurve.data_path)
            if display_props.show_channel_name
            else None
        )

        info_str = ""
        if object_name:
            info_str += f"< {object_name} >"
        if action_name:
            info_str += f"< {action_name} >"
        if group_name:
            info_str += f"< {group_name} >"
        if channel_name:
            info_str += f" {channel_name} >"

        info_str = info_str.replace("><", "|")

        return info_str

    return None


class GRAPH_OT_monkey_handle_selecter(bpy.types.Operator):
    bl_idname = "graph.monkey_handle_selecter"
    bl_label = "Toggle Handle Selection"
    bl_options = {"REGISTER", "UNDO"}

    handle_direction: bpy.props.EnumProperty(
        name="Handle Direction",
        items=[("Left", "Left", ""), ("Right", "Right", "")],
        default="Left",
    )
    extend: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        if context.area.type != "GRAPH_EDITOR":
            return False

        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        return bool(visible_objects)

    def execute(self, context):
        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        toggle_handle_selection(self.handle_direction, self.extend, visible_objects)
        return {"FINISHED"}


def toggle_handle_selection(handle_direction, extend, visible_objects):
    if visible_objects is None:
        return

    all_selected = True

    for obj in visible_objects:
        selected_channels = [
            fcurve for fcurve in obj.animation_data.action.fcurves if fcurve.select
        ]

        if selected_channels:
            all_selected &= all_keyframes_have_selected_handle(obj, handle_direction)
            if not all_selected:
                break

    for obj in visible_objects:
        selected_channels = [
            fcurve for fcurve in obj.animation_data.action.fcurves if fcurve.select
        ]

        if selected_channels:
            toggle_keyframe_handle_selection(
                obj, handle_direction, extend, all_selected
            )


def all_keyframes_have_selected_handle(obj, handle_direction):
    action = obj.animation_data.action

    for fcurve in action.fcurves:
        if not fcurve.select:
            continue

        selected = get_selected_keyframes(fcurve.keyframe_points)

        if not selected:
            continue

        for item in selected:
            keyframe = item["keyframe"]

            if handle_direction == "Left":
                if not keyframe.select_left_handle:
                    return False
            elif handle_direction == "Right":
                if not keyframe.select_right_handle:
                    return False
    return True


def toggle_keyframe_handle_selection(obj, handle_direction, extend, all_selected):
    action = obj.animation_data.action

    for fcurve in action.fcurves:
        if not fcurve.select:
            continue

        selected = get_selected_keyframes(fcurve.keyframe_points)

        if not selected:
            continue

        for item in selected:
            keyframe = item["keyframe"]
            update_keyframe_handle_selection(
                keyframe, handle_direction, extend, all_selected
            )


def update_keyframe_handle_selection(keyframe, handle_direction, extend, all_selected):
    if handle_direction == "Left":
        if all_selected:
            keyframe.select_left_handle = False
            keyframe.select_control_point = True
        else:
            if not extend:
                keyframe.select_right_handle = False
                keyframe.select_control_point = False
            keyframe.select_left_handle = True
    elif handle_direction == "Right":
        if all_selected:
            keyframe.select_right_handle = False
            keyframe.select_control_point = True
        else:
            if not extend:
                keyframe.select_left_handle = False
                keyframe.select_control_point = False
            keyframe.select_right_handle = True


class GRAPH_OT_select_adjacent_handles(bpy.types.Operator):
    bl_idname = "graph.select_adjacent_handles"
    bl_label = "Select Adjacent Handles"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.area.type != "GRAPH_EDITOR":
            return False

        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        return bool(visible_objects)

    def execute(self, context):
        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        select_adjacent_handles(visible_objects)
        return {"FINISHED"}


def select_adjacent_handles(visible_objects):
    if visible_objects is None:
        return

    for obj in visible_objects:
        selected_channels = [
            fcurve for fcurve in obj.animation_data.action.fcurves if fcurve.select
        ]

        if selected_channels:
            for fcurve in selected_channels:
                select_keyframe_handles(fcurve)


def select_keyframe_handles(fcurve):
    keyframe_points = fcurve.keyframe_points
    selected_keyframes = [
        i for i, keyframe in enumerate(keyframe_points) if keyframe.select_control_point
    ]

    for i in selected_keyframes:
        keyframe = keyframe_points[i]
        keyframe.select_right_handle = True
        keyframe.select_control_point = False
        if i + 1 < len(keyframe_points):
            next_keyframe = keyframe_points[i + 1]
            next_keyframe.select_left_handle = True
            next_keyframe.select_control_point = False

            # Select the right handle of the next keyframe if it's also selected
            if (i + 1) in selected_keyframes:
                next_keyframe.select_right_handle = True


# def check_graph_editor_and_visible_objects():
#     graph_editor = None
#     for area in bpy.context.screen.areas:
#         if area.type == 'GRAPH_EDITOR':
#             graph_editor = area.spaces.active
#             break

#     if graph_editor is None:
#         print("Graph Editor not found.")
#         return None, None

#     dopesheet = graph_editor.dopesheet

#     visible_objects = get_visible_objects(dopesheet)

#     if not visible_objects:
#         print("There is no object that is displayed and has an action.")
#         return None, None

#     return graph_editor, visible_objects


def is_object_displayed(obj, dopesheet, type_filters):
    # Check if the object's type is shown
    obj_type = obj.type
    if obj_type in type_filters and not type_filters[obj_type]:
        return False

    # Check if the object is selected
    if dopesheet.show_only_selected and not obj.select_get():
        return False

    # Check if the object is hidden
    if not dopesheet.show_hidden and obj.hide_viewport:
        return False

    return True


def get_visible_objects(dopesheet):
    type_filters = {
        "SCENE": dopesheet.show_scenes,
        "NODETREE": dopesheet.show_nodes,
        "CAMERA": dopesheet.show_cameras,
        "LIGHT": dopesheet.show_lights,
        "MESH": dopesheet.show_meshes,
        "WORLD": dopesheet.show_worlds,
        "LINESTYLE": dopesheet.show_linestyles,
        "MATERIAL": dopesheet.show_materials,
    }
    visible_objects = [
        obj
        for obj in bpy.context.scene.objects
        if obj.animation_data
        and obj.animation_data.action
        and is_object_displayed(obj, dopesheet, type_filters)
    ]
    visible_objects.sort(key=lambda obj: obj.name)
    return visible_objects


def get_selected_keyframes(keyframe_points):
    return [
        {
            "keyframe": keyframe,
            "control_point": keyframe.select_control_point,
            "left_handle": keyframe.select_left_handle,
            "right_handle": keyframe.select_right_handle,
        }
        for keyframe in keyframe_points
        if keyframe.select_control_point
        or keyframe.select_left_handle
        or keyframe.select_right_handle
    ]


def move_keyframe_selection_horizontally(
    direction="forward", extend=False, visible_objects=None
):
    if visible_objects is None:
        return

    for obj in visible_objects:
        selected_channels = [
            fcurve for fcurve in obj.animation_data.action.fcurves if fcurve.select
        ]

        if selected_channels:
            process_keyframe_selection_for_horizontal_move(obj, direction, extend)


def process_keyframe_selection_for_horizontal_move(
    obj, direction="forward", extend=False
):
    if direction not in ("forward", "backward"):
        raise ValueError(
            "Invalid value for direction. Must be 'forward' or 'backward'."
        )

    action = obj.animation_data.action

    for fcurve in action.fcurves:
        if not fcurve.select:  # Only process selected fcurves
            continue

        selected = get_selected_keyframes(fcurve.keyframe_points)

        if not selected:
            continue

        if direction == "forward":
            selected.sort(key=lambda k: k["keyframe"].co[0], reverse=True)
        else:  # direction == "backward"
            selected.sort(key=lambda k: k["keyframe"].co[0])

        for item in selected:
            keyframe = item["keyframe"]
            if direction == "forward":
                target_frame = keyframe.co[0] + 1
            else:  # direction == "backward"
                target_frame = keyframe.co[0] - 1

            next_keyframe = binary_search_keyframe(fcurve, target_frame, direction)

            if next_keyframe is not None:
                transfer_keyframe_selection([item], [next_keyframe], extend)


def binary_search_keyframe(fcurve, target_frame, direction="forward"):
    left = 0
    right = len(fcurve.keyframe_points) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_frame = fcurve.keyframe_points[mid].co[0]

        if mid_frame == target_frame:
            return fcurve.keyframe_points[mid]
        elif mid_frame < target_frame:
            left = mid + 1
        else:
            right = mid - 1

    if direction == "forward" and left < len(fcurve.keyframe_points):
        return fcurve.keyframe_points[left]
    elif direction == "backward" and right >= 0:
        return fcurve.keyframe_points[right]

    return None


def move_channel_selection_vertically(
    direction="downward", extend=False, visible_objects=None
):
    if direction not in ("downward", "upward"):
        raise ValueError("Invalid value for direction. Must be 'downward' or 'upward'.")

    if visible_objects is None:
        return

    all_fcurves = []

    for obj in visible_objects:
        action = obj.animation_data.action
        all_fcurves.extend(action.fcurves)

    num_fcurves = len(all_fcurves)

    selected_indices = [i for i, fcurve in enumerate(all_fcurves) if fcurve.select]

    if direction == "downward":
        selected_indices.sort(reverse=True)
    else:  # direction == "upward"
        selected_indices.sort()

    for current_index in selected_indices:
        fcurve = all_fcurves[current_index]

        if direction == "downward":
            next_index = current_index + 1
        else:  # direction == "upward"
            next_index = current_index - 1

        if 0 <= next_index < num_fcurves:
            next_fcurve = all_fcurves[next_index]
            process_keyframe_selection_for_vertical_move(fcurve, next_fcurve, extend)


def process_keyframe_selection_for_vertical_move(fcurve_from, fcurve_to, extend=False):
    selected = get_selected_keyframes(fcurve_from.keyframe_points)

    if not extend:
        fcurve_from.select = False

    fcurve_to.select = True

    # Move the selection to the nearest keyframes in the new channel
    for item in selected:
        target_keyframes = [
            min(
                fcurve_to.keyframe_points,
                key=lambda k: abs(k.co[0] - item["keyframe"].co[0]),
            )
            for item in selected
        ]

        transfer_keyframe_selection(selected, target_keyframes, extend)


def transfer_keyframe_selection(selected, target_keyframes, extend=False):
    for item, target_keyframe in zip(selected, target_keyframes):
        keyframe = item["keyframe"]

        if not extend:
            keyframe.select_control_point = False
        target_keyframe.select_control_point = item["control_point"]

        if (
            keyframe.interpolation == "BEZIER"
            and target_keyframe.interpolation == "BEZIER"
        ):
            if item["left_handle"]:
                target_keyframe.select_left_handle = True
                if not extend:
                    keyframe.select_left_handle = False
            if item["right_handle"]:
                target_keyframe.select_right_handle = True
                if not extend:
                    keyframe.select_right_handle = False


class MonKeyPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    forward_key: bpy.props.StringProperty(name="Forward Key", default="D")
    forward_key_extend: bpy.props.StringProperty(
        name="Forward Key (Extend)", default="D"
    )
    backward_key: bpy.props.StringProperty(name="Backward Key", default="A")
    backward_key_extend: bpy.props.StringProperty(
        name="Backward Key (Extend)", default="A"
    )
    upward_key: bpy.props.StringProperty(name="Upward Key", default="W")
    upward_key_extend: bpy.props.StringProperty(name="Upward Key (Extend)", default="W")
    downward_key: bpy.props.StringProperty(name="Downward Key", default="S")
    downward_key_extend: bpy.props.StringProperty(
        name="Downward Key (Extend)", default="S"
    )

    # def draw(self, context):
    #     layout = self.layout
    #     layout.label(text="Key Bindings:")

    #     col = layout.column(align=True)
    #     col.prop(self, "upward_key")
    #     col.prop(self, "upward_key_extend")

    #     col = layout.column(align=True)
    #     col.prop(self, "forward_key")
    #     col.prop(self, "forward_key_extend")

    #     col = layout.column(align=True)
    #     col.prop(self, "backward_key")
    #     col.prop(self, "backward_key_extend")

    #     col = layout.column(align=True)
    #     col.prop(self, "downward_key")
    #     col.prop(self, "downward_key_extend")


addon_keymaps = []


def register_keymaps():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Graph Editor", space_type="GRAPH_EDITOR")

    preferences = bpy.context.preferences.addons[__name__].preferences

    # Upward
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_vertically.bl_idname,
        type=preferences.upward_key,
        value="PRESS",
        alt=True,
    )
    kmi.properties.direction = "upward"
    kmi.properties.extend = False

    # Upward Extend
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_vertically.bl_idname,
        type=preferences.upward_key_extend,
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "upward"
    kmi.properties.extend = True

    # Downward
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_vertically.bl_idname,
        type=preferences.downward_key,
        value="PRESS",
        alt=True,
    )
    kmi.properties.direction = "downward"
    kmi.properties.extend = False

    # Downward Extend
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_vertically.bl_idname,
        type=preferences.downward_key_extend,
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "downward"
    kmi.properties.extend = True

    # Forward
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_horizontally.bl_idname,
        type=preferences.forward_key,
        value="PRESS",
        alt=True,
    )
    kmi.properties.direction = "forward"
    kmi.properties.extend = False

    # Forward Extend
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_horizontally.bl_idname,
        type=preferences.forward_key_extend,
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "forward"
    kmi.properties.extend = True

    # Backward
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_horizontally.bl_idname,
        type=preferences.backward_key,
        value="PRESS",
        alt=True,
    )
    kmi.properties.direction = "backward"
    kmi.properties.extend = False

    # Backward Extend
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_horizontally.bl_idname,
        type=preferences.backward_key_extend,
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.direction = "backward"
    kmi.properties.extend = True

    # Left
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_handle_selecter.bl_idname, type="Q", value="PRESS", alt=True
    )
    kmi.properties.handle_direction = "Left"
    kmi.properties.extend = False

    # Left Extend
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_handle_selecter.bl_idname,
        type="Q",
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.handle_direction = "Left"
    kmi.properties.extend = True

    # Right
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_handle_selecter.bl_idname, type="E", value="PRESS", alt=True
    )
    kmi.properties.handle_direction = "Right"
    kmi.properties.extend = False

    # Right Extend
    kmi = km.keymap_items.new(
        GRAPH_OT_monkey_handle_selecter.bl_idname,
        type="E",
        value="PRESS",
        alt=True,
        shift=True,
    )
    kmi.properties.handle_direction = "Right"
    kmi.properties.extend = True

    # Select Adjacent Handles
    kmi = km.keymap_items.new(
        GRAPH_OT_select_adjacent_handles.bl_idname,
        type="E",
        value="PRESS",
        ctrl=True,
        alt=True,
    )

    addon_keymaps.append(km)


def unregister_keymaps():
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()


# # Update register and unregister functions
# def register():
#     bpy.utils.register_class(GRAPH_OT_monkey_horizontally)
#     bpy.utils.register_class(GRAPH_OT_monkey_vertically)
#     bpy.utils.register_class(GRAPH_OT_monkey_handle_selecter)
#     bpy.utils.register_class(GRAPH_OT_draw_text)
#     bpy.utils.register_class(GRAPH_OT_select_adjacent_handles)
#     # bpy.utils.register_class(MonKeyDisplayProperties)
#     bpy.utils.register_class(MonKeyPreferences)
#     register_keymaps()

# def unregister():
#     unregister_keymaps()
#     bpy.utils.unregister_class(MonKeyPreferences)
#     # bpy.utils.unregister_class(MonKeyDisplayProperties)
#     bpy.utils.unregister_class(GRAPH_OT_select_adjacent_handles)
#     bpy.utils.unregister_class(GRAPH_OT_draw_text)
#     bpy.utils.unregister_class(GRAPH_OT_monkey_handle_selecter)
#     bpy.utils.unregister_class(GRAPH_OT_monkey_vertically)
#     bpy.utils.unregister_class(GRAPH_OT_monkey_horizontally)


if __name__ == "__main__":
    pass

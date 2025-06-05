# Add Action creation and unlink tools to Graph Editor
# Location: Graph Editor > Header

import bpy
from bpy.types import GRAPH_MT_editor_menus, Operator
from bpy.app import version as BL_VERSION


class GRAPH_EDITOR_OT_create_action(Operator):
    bl_idname = "graph_editor.create_action"
    bl_label = "New Action"
    bl_description = "Create a new action in Graph Editor"

    def execute(self, context):
        obj = context.active_object

        if obj is not None:
            if obj.animation_data is None:
                obj.animation_data_create()

            current_action = obj.animation_data.action
            if current_action:
                new_action = current_action.copy()
            else:
                new_action = bpy.data.actions.new(name="Action")

            obj.animation_data.action = new_action
        else:
            self.report({"WARNING"}, "No active object.")

        return {"FINISHED"}


class GRAPH_EDITOR_OT_unlink_action(Operator):
    bl_idname = "graph_editor.unlink_action"
    bl_label = "Unlink Action"
    bl_description = "Unlink action in Graph Editor"

    def execute(self, context):
        obj = context.active_object

        if obj is not None and obj.animation_data is not None:
            action = obj.animation_data.action
            if action and not action.use_fake_user and not action.id_root in {"NLA"}:
                self.report(
                    {"WARNING"},
                    f"Action '{action.name}' will not be saved, create Fake User or Stash in NLA Stack to retain",
                )

            obj.animation_data.action = None
        else:
            self.report({"WARNING"}, "No action to unlink.")

        return {"FINISHED"}


# class GRAPH_EDITOR_OT_layer_prev(Operator):
#     bl_idname = "graph_editor.layer_prev"
#     bl_label = "Previous Layer"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.layer_prev(override)

# class GRAPH_EDITOR_OT_layer_next(Operator):
#     bl_idname = "graph_editor.layer_next"
#     bl_label = "Next Layer"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.layer_next(override)

# class GRAPH_EDITOR_OT_push_down(Operator):
#     bl_idname = "graph_editor.push_down"
#     bl_label = "Push Down"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.push_down(override)

# class GRAPH_EDITOR_OT_stash(Operator):
#     bl_idname = "graph_editor.stash"
#     bl_label = "Stash"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.stash(override, create_new=True)


def _get_animated_id(context):
    """Get the animated ID for the current context"""
    return context.object


def _draw_action_selector(context, layout):
    """Draw action and action slot selector similar to DopeSheet"""
    animated_id = _get_animated_id(context)
    if not animated_id:
        return

    row = layout.row()
    if animated_id.animation_data and animated_id.animation_data.use_tweak_mode:
        row.enabled = False

    # Action selector
    row.template_action(animated_id, new="graph_editor.create_action", unlink="graph_editor.unlink_action")

    # Action slot selector for layered actions (Blender 4.4+ only)
    if BL_VERSION >= (4, 4, 0):
        adt = animated_id and animated_id.animation_data
        if not adt or not adt.action:
            return
        
        # Check if action has is_action_layered attribute (safer check)
        if hasattr(adt.action, 'is_action_layered') and adt.action.is_action_layered:
            row.context_pointer_set("animated_id", animated_id)
            row.template_search(
                adt, "action_slot",
                adt, "action_suitable_slots",
                new="anim.slot_new_for_id",
                unlink="anim.slot_unassign_from_id",
            )


def draw_func(self, context):
    layout = self.layout

    if BL_VERSION >= (4, 4, 0):
        layout.menu("DOPESHEET_MT_action")
        # TODO: 以下のオペレーターをグラフエディタで利用できるようにする。
        # bpy.ops.anim.slot_channels_move_to_new_action()
        # bpy.ops.action.push_down()
        # bpy.ops.action.stash()

    obj = context.active_object
    layout.separator()

    # layout.operator("graph_editor.layer_prev", text="", icon='TRIA_DOWN')
    # layout.operator("graph_editor.layer_next", text="", icon='TRIA_UP')

    # layout.separator()

    # layout.operator("graph_editor.push_down", text="", icon='NLA_PUSHDOWN')
    # layout.operator("graph_editor.stash", text="", icon='FREEZE')

    # layout.separator()

    if obj is not None:
        if obj.animation_data is None:
            obj.animation_data_create()

        # Use the new action selector that supports action slots
        _draw_action_selector(context, layout)
    else:
        layout.label("No active object", icon="ERROR")


def register():
    GRAPH_MT_editor_menus.append(draw_func)


def unregister():
    GRAPH_MT_editor_menus.remove(draw_func)

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


class GRAPH_EDITOR_OT_push_down(Operator):
    bl_idname = "graph_editor.push_down"
    bl_label = "Push Down"
    bl_description = "Push down action to NLA stack from Graph Editor"

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No action to push down")
            return {'CANCELLED'}

        # Get current area (should be Graph Editor)
        current_area = context.area
        if not current_area:
            self.report({'WARNING'}, "No area context")
            return {'CANCELLED'}

        # Store original area type
        original_area_type = current_area.type
        
        try:
            # Temporarily change area to DOPESHEET_EDITOR
            current_area.type = 'DOPESHEET_EDITOR'
            
            # Set dopesheet mode to ACTION
            dopesheet_space = current_area.spaces.active
            dopesheet_space.mode = 'ACTION'
            
            # Execute push down with proper context
            with context.temp_override(
                area=current_area,
                space_data=dopesheet_space,
                object=obj,
                active_object=obj,
                selected_objects=[obj] if obj else [],
            ):
                result = bpy.ops.action.push_down()
            return result
            
        except Exception as e:
            self.report({'WARNING'}, f"Cannot push down action: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Always restore original area type
            current_area.type = original_area_type


class GRAPH_EDITOR_OT_stash(Operator):
    bl_idname = "graph_editor.stash"
    bl_label = "Stash"
    bl_description = "Stash action in NLA stack from Graph Editor"

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "No action to stash")
            return {'CANCELLED'}

        # Get current area (should be Graph Editor)
        current_area = context.area
        if not current_area:
            self.report({'WARNING'}, "No area context")
            return {'CANCELLED'}

        # Store original area type
        original_area_type = current_area.type
        
        try:
            # Temporarily change area to DOPESHEET_EDITOR
            current_area.type = 'DOPESHEET_EDITOR'
            
            # Set dopesheet mode to ACTION
            dopesheet_space = current_area.spaces.active
            dopesheet_space.mode = 'ACTION'
            
            # Execute stash with proper context
            with context.temp_override(
                area=current_area,
                space_data=dopesheet_space,
                object=obj,
                active_object=obj,
                selected_objects=[obj] if obj else [],
            ):
                result = bpy.ops.action.stash(create_new=True)
            return result
            
        except Exception as e:
            self.report({'WARNING'}, f"Cannot stash action: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Always restore original area type
            current_area.type = original_area_type


class GRAPH_EDITOR_OT_slot_channels_move_to_new_action(Operator):
    bl_idname = "graph_editor.slot_channels_move_to_new_action"
    bl_label = "Move Channels to New Action"
    bl_description = "Move selected channels to new action from Graph Editor"

    @classmethod
    def poll(cls, context):
        return BL_VERSION >= (4, 4, 0) and context.active_object and context.active_object.animation_data

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "No animation data")
            return {'CANCELLED'}

        # Get current area (should be Graph Editor)
        current_area = context.area
        if not current_area:
            self.report({'WARNING'}, "No area context")
            return {'CANCELLED'}

        # Store original area type
        original_area_type = current_area.type
        
        try:
            # Temporarily change area to DOPESHEET_EDITOR
            current_area.type = 'DOPESHEET_EDITOR'
            
            # Set dopesheet mode to ACTION
            dopesheet_space = current_area.spaces.active
            dopesheet_space.mode = 'ACTION'
            
            # Execute move channels with proper context
            with context.temp_override(
                area=current_area,
                space_data=dopesheet_space,
                object=obj,
                active_object=obj,
                selected_objects=[obj] if obj else [],
            ):
                result = bpy.ops.anim.slot_channels_move_to_new_action()
            return result
            
        except Exception as e:
            self.report({'WARNING'}, f"Cannot move channels: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Always restore original area type
            current_area.type = original_area_type


class GRAPH_EDITOR_OT_layer_prev(Operator):
    bl_idname = "graph_editor.layer_prev"
    bl_label = "Previous Layer"
    bl_description = "Switch to previous action layer from Graph Editor"

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.animation_data)

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "No animation data")
            return {'CANCELLED'}

        # Get current area (should be Graph Editor)
        current_area = context.area
        if not current_area:
            self.report({'WARNING'}, "No area context")
            return {'CANCELLED'}

        # Store original area type
        original_area_type = current_area.type
        
        try:
            # Temporarily change area to DOPESHEET_EDITOR
            current_area.type = 'DOPESHEET_EDITOR'
            
            # Set dopesheet mode to ACTION
            dopesheet_space = current_area.spaces.active
            dopesheet_space.mode = 'ACTION'
            
            # Execute layer prev with proper context
            with context.temp_override(
                area=current_area,
                space_data=dopesheet_space,
                object=obj,
                active_object=obj,
                selected_objects=[obj] if obj else [],
            ):
                result = bpy.ops.action.layer_prev()
                
            return result
            
        except Exception as e:
            self.report({'WARNING'}, f"Cannot switch to previous layer: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Always restore original area type
            current_area.type = original_area_type


class GRAPH_EDITOR_OT_layer_next(Operator):
    bl_idname = "graph_editor.layer_next"
    bl_label = "Next Layer"
    bl_description = "Switch to next action layer from Graph Editor"

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.animation_data)

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.animation_data:
            self.report({'WARNING'}, "No animation data")
            return {'CANCELLED'}

        # Get current area (should be Graph Editor)
        current_area = context.area
        if not current_area:
            self.report({'WARNING'}, "No area context")
            return {'CANCELLED'}

        # Store original area type
        original_area_type = current_area.type
        
        try:
            # Temporarily change area to DOPESHEET_EDITOR
            current_area.type = 'DOPESHEET_EDITOR'
            
            # Set dopesheet mode to ACTION
            dopesheet_space = current_area.spaces.active
            dopesheet_space.mode = 'ACTION'
            
            # Execute layer next with proper context
            with context.temp_override(
                area=current_area,
                space_data=dopesheet_space,
                object=obj,
                active_object=obj,
                selected_objects=[obj] if obj else [],
            ):
                result = bpy.ops.action.layer_next()
                
            return result
            
        except Exception as e:
            self.report({'WARNING'}, f"Cannot switch to next layer: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Always restore original area type
            current_area.type = original_area_type


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
    row = layout.row(align=True)

    if BL_VERSION >= (4, 4, 0):
        row.menu("DOPESHEET_MT_action")

        # Action management operators for layered actions        
        row.operator("graph_editor.slot_channels_move_to_new_action", text="", icon='DUPLICATE')

    row.operator("graph_editor.push_down", text="", icon='NLA_PUSHDOWN')
    row.operator("graph_editor.stash", text="", icon='FREEZE')

    row.operator("graph_editor.layer_prev", text="", icon='TRIA_DOWN')
    row.operator("graph_editor.layer_next", text="", icon='TRIA_UP')

    obj = context.active_object
    layout.separator()

    if obj is not None:
        if obj.animation_data is None:
            obj.animation_data_create()
        
        # Use the new action selector that supports action slots
        _draw_action_selector(context, layout)
    else:
        layout.label(text="No active object", icon="ERROR")


def register():
    GRAPH_MT_editor_menus.append(draw_func)


def unregister():
    GRAPH_MT_editor_menus.remove(draw_func)

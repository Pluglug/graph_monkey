bl_info = {
    "name": "Graph Editor Action Tools",
    "author": "Pluglug",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Graph Editor > Header",
    "description": "Add Action creation and unlink tools to Graph Editor",
    "category": "Animation",
}

import bpy


class GRAPH_EDITOR_OT_create_action(bpy.types.Operator):
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
            self.report({'WARNING'}, "No active object.")

        return {'FINISHED'}


class GRAPH_EDITOR_OT_unlink_action(bpy.types.Operator):
    bl_idname = "graph_editor.unlink_action"
    bl_label = "Unlink Action"
    bl_description = "Unlink action in Graph Editor"

    def execute(self, context):
        obj = context.active_object

        if obj is not None and obj.animation_data is not None:
            action = obj.animation_data.action
            if action and not action.use_fake_user and not action.id_root in {'NLA'}:
                self.report(
                    {'WARNING'},
                    f"Action '{action.name}' will not be saved, create Fake User or Stash in NLA Stack to retain"
                )

            obj.animation_data.action = None
        else:
            self.report({'WARNING'}, "No action to unlink.")

        return {'FINISHED'}


# class GRAPH_EDITOR_OT_layer_prev(bpy.types.Operator):
#     bl_idname = "graph_editor.layer_prev"
#     bl_label = "Previous Layer"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.layer_prev(override)

# class GRAPH_EDITOR_OT_layer_next(bpy.types.Operator):
#     bl_idname = "graph_editor.layer_next"
#     bl_label = "Next Layer"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.layer_next(override)

# class GRAPH_EDITOR_OT_push_down(bpy.types.Operator):
#     bl_idname = "graph_editor.push_down"
#     bl_label = "Push Down"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.push_down(override)

# class GRAPH_EDITOR_OT_stash(bpy.types.Operator):
#     bl_idname = "graph_editor.stash"
#     bl_label = "Stash"

#     def invoke(self, context, event):
#         override = context.copy()
#         dopesheet_area = [area for area in context.screen.areas if area.type == 'DOPESHEET_EDITOR'][0]
#         override['area'] = dopesheet_area
#         override['space_data'] = dopesheet_area.spaces.active
#         return bpy.ops.action.stash(override, create_new=True)


def draw_func(self, context):
    layout = self.layout
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
        ad = obj.animation_data
        layout.template_ID(
            ad, 'action', new='graph_editor.create_action', unlink='graph_editor.unlink_action'
        )
    else:
        layout.label("No active object", icon='ERROR')


def register():
    bpy.utils.register_class(GRAPH_EDITOR_OT_create_action)
    bpy.utils.register_class(GRAPH_EDITOR_OT_unlink_action)
    # bpy.utils.register_class(GRAPH_EDITOR_OT_layer_prev)
    # bpy.utils.register_class(GRAPH_EDITOR_OT_layer_next)
    # bpy.utils.register_class(GRAPH_EDITOR_OT_push_down)
    # bpy.utils.register_class(GRAPH_EDITOR_OT_stash)
    bpy.types.GRAPH_MT_editor_menus.append(draw_func)


def unregister():
    bpy.utils.unregister_class(GRAPH_EDITOR_OT_create_action)
    bpy.utils.unregister_class(GRAPH_EDITOR_OT_unlink_action)
    # bpy.utils.unregister_class(GRAPH_EDITOR_OT_layer_prev)
    # bpy.utils.unregister_class(GRAPH_EDITOR_OT_layer_next)
    # bpy.utils.unregister_class(GRAPH_EDITOR_OT_push_down)
    # bpy.utils.unregister_class(GRAPH_EDITOR_OT_stash)
    bpy.types.GRAPH_MT_editor_menus.remove(draw_func)


if __name__ == "__main__":
    register()

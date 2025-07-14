# import bpy
# from bpy.types import Panel, PropertyGroup
# from bpy.props import StringProperty, BoolProperty, EnumProperty
# from .keymap_manager import keymap_registry, keymap_config

# class MonKeyKeymapSettings(PropertyGroup):
#     """MonKeyキーマップ設定プロパティ"""
    
#     # 垂直移動キー
#     vertical_upward_key: StringProperty(
#         name="Upward",
#         description="Key for upward channel movement",
#         default="W",
#         maxlen=1
#     )
#     vertical_downward_key: StringProperty(
#         name="Downward", 
#         description="Key for downward channel movement",
#         default="S",
#         maxlen=1
#     )
    
#     # 水平移動キー
#     horizontal_forward_key: StringProperty(
#         name="Forward",
#         description="Key for forward keyframe movement", 
#         default="D",
#         maxlen=1
#     )
#     horizontal_backward_key: StringProperty(
#         name="Backward",
#         description="Key for backward keyframe movement",
#         default="A", 
#         maxlen=1
#     )
    
#     # ハンドル選択キー
#     handle_left_key: StringProperty(
#         name="Left Handle",
#         description="Key for left handle selection",
#         default="Q",
#         maxlen=1
#     )
#     handle_right_key: StringProperty(
#         name="Right Handle", 
#         description="Key for right handle selection",
#         default="E",
#         maxlen=1
#     )
    
#     # ビューコントロールキー
#     view_focus_key: StringProperty(
#         name="Focus",
#         description="Key for focus selected curves",
#         default="F",
#         maxlen=1
#     )
    
#     # 詳細設定
#     use_alt_modifier: BoolProperty(
#         name="Use Alt Modifier",
#         description="Require Alt key for all shortcuts",
#         default=True
#     )
    
#     auto_apply_changes: BoolProperty(
#         name="Auto Apply Changes",
#         description="Automatically apply keymap changes",
#         default=True
#     )
    
#     def update_keymaps(self, context):
#         """キーマップ設定を更新"""
#         if not self.auto_apply_changes:
#             return
            
#         # 設定をkeymap_configに反映
#         config = keymap_config
#         config.set_key_for_action("vertical_movement", "upward", self.vertical_upward_key)
#         config.set_key_for_action("vertical_movement", "downward", self.vertical_downward_key)
#         config.set_key_for_action("horizontal_movement", "forward", self.horizontal_forward_key)
#         config.set_key_for_action("horizontal_movement", "backward", self.horizontal_backward_key)
#         config.set_key_for_action("handle_selection", "left", self.handle_left_key)
#         config.set_key_for_action("handle_selection", "right", self.handle_right_key)
#         config.set_key_for_action("view_control", "focus", self.view_focus_key)
        
#         # キーマップを再適用
#         keymap_registry.apply_keymaps()

# class MONKEY_OT_apply_keymaps(bpy.types.Operator):
#     """Apply keymap changes"""
#     bl_idname = "monkey.apply_keymaps"
#     bl_label = "Apply Keymap Changes"
#     bl_description = "Apply current keymap settings"
    
#     def execute(self, context):
#         prefs = context.preferences.addons[__name__.split('.')[0]].preferences
#         if hasattr(prefs, 'keymap_settings'):
#             prefs.keymap_settings.update_keymaps(context)
#             self.report({'INFO'}, "Keymap changes applied")
#         return {'FINISHED'}

# class MONKEY_OT_reset_keymaps(bpy.types.Operator):
#     """Reset keymaps to default"""
#     bl_idname = "monkey.reset_keymaps"
#     bl_label = "Reset to Default"
#     bl_description = "Reset all keymap settings to default values"
    
#     def execute(self, context):
#         prefs = context.preferences.addons[__name__.split('.')[0]].preferences
#         if hasattr(prefs, 'keymap_settings'):
#             settings = prefs.keymap_settings
#             settings.vertical_upward_key = "W"
#             settings.vertical_downward_key = "S"
#             settings.horizontal_forward_key = "D"
#             settings.horizontal_backward_key = "A"
#             settings.handle_left_key = "Q"
#             settings.handle_right_key = "E"
#             settings.view_focus_key = "F"
#             settings.update_keymaps(context)
#             self.report({'INFO'}, "Keymap settings reset to default")
#         return {'FINISHED'}

# class MONKEY_OT_check_conflicts(bpy.types.Operator):
#     """Check for keymap conflicts"""
#     bl_idname = "monkey.check_conflicts"
#     bl_label = "Check Conflicts"
#     bl_description = "Check for keymap conflicts"
    
#     def execute(self, context):
#         conflicts = keymap_registry.check_conflicts()
#         if conflicts:
#             conflict_msg = "Keymap conflicts found:\n" + "\n".join([f"• {c1} vs {c2}" for c1, c2 in conflicts])
#             self.report({'WARNING'}, conflict_msg)
#         else:
#             self.report({'INFO'}, "No keymap conflicts found")
#         return {'FINISHED'}

# class MONKEY_PT_keymap_settings(Panel):
#     """MonKey Keymap Settings Panel"""
#     bl_label = "MonKey Keymap Settings"
#     bl_idname = "MONKEY_PT_keymap_settings"
#     bl_space_type = 'PREFERENCES'
#     bl_region_type = 'WINDOW'
#     bl_context = "addons"
    
#     @classmethod
#     def poll(cls, context):
#         return context.preferences.active_section == 'ADDONS'
    
#     def draw(self, context):
#         layout = self.layout
#         prefs = context.preferences.addons[__name__.split('.')[0]].preferences
        
#         if not hasattr(prefs, 'keymap_settings'):
#             layout.label(text="Keymap settings not available", icon='ERROR')
#             return
            
#         settings = prefs.keymap_settings
        
#         # メインカラム
#         col = layout.column()
        
#         # 基本設定
#         box = col.box()
#         box.label(text="Basic Settings", icon='PREFERENCES')
#         box.prop(settings, "use_alt_modifier")
#         box.prop(settings, "auto_apply_changes")
        
#         # 垂直移動設定
#         box = col.box()
#         box.label(text="Vertical Movement", icon='CON_TRANSLIKE')
#         row = box.row()
#         row.prop(settings, "vertical_upward_key")
#         row.prop(settings, "vertical_downward_key")
        
#         # 水平移動設定
#         box = col.box()
#         box.label(text="Horizontal Movement", icon='CON_LOCLIKE')
#         row = box.row()
#         row.prop(settings, "horizontal_forward_key")
#         row.prop(settings, "horizontal_backward_key")
        
#         # ハンドル選択設定
#         box = col.box()
#         box.label(text="Handle Selection", icon='HANDLE_FREE')
#         row = box.row()
#         row.prop(settings, "handle_left_key")
#         row.prop(settings, "handle_right_key")
        
#         # ビューコントロール設定
#         box = col.box()
#         box.label(text="View Control", icon='VIEW_CAMERA')
#         box.prop(settings, "view_focus_key")
        
#         # アクションボタン
#         col.separator()
#         row = col.row()
#         row.operator("monkey.apply_keymaps", icon='FILE_REFRESH')
#         row.operator("monkey.reset_keymaps", icon='LOOP_BACK')
#         row.operator("monkey.check_conflicts", icon='ERROR')

# # 登録用クラスリスト
# classes = [
#     MonKeyKeymapSettings,
#     MONKEY_OT_apply_keymaps,
#     MONKEY_OT_reset_keymaps, 
#     MONKEY_OT_check_conflicts,
#     MONKEY_PT_keymap_settings,
# ]

# def register():
#     for cls in classes:
#         bpy.utils.register_class(cls)

# def unregister():
#     for cls in reversed(classes):
#         bpy.utils.unregister_class(cls) 
"""
Graph EditorとDriversのNパネルにF-Curves設定パネルを追加。

主な機能:
- PreferencesのF-Curves設定に素早くアクセス
- Graph EditorとDriversの両方で利用可能

使用例: アニメーション作業中に補間設定を素早く変更したい時
"""

import bpy
from bpy.types import Panel


class GRAPH_PT_fcurves_prefs(Panel):
    """Graph Editor/DriversのNパネルにF-Curves設定を表示"""

    bl_label = "F-Curves"
    bl_idname = "GRAPH_PT_fcurves_prefs"
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"
    bl_category = "View"

    def draw(self, context):
        # BlenderのUSERPREF_PT_animation_fcurvesパネルのdraw_centeredメソッドを呼び出す
        prefs_panel = bpy.types.USERPREF_PT_animation_fcurves
        prefs_panel.draw_centered(None, context, self.layout)

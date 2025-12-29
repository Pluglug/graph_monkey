# pyright: reportInvalidTypeForm=false
"""
Topbar Menu Manager
トップバーに個人用メニューを追加するモジュール

機能:
- TOPBAR_MT_pluglug: 個人用メニュー（拡張可能）
- .blendファイル内のテキストスクリプトを実行

使用例: リグ付属のスクリプト（rig_ui.py等）をテキストエディタを開かずに実行
"""

import bpy
from bpy.types import Menu, Operator
from bpy.props import StringProperty

from ..utils.logging import get_logger

log = get_logger(__name__)


# =============================================================================
# オペレーター
# =============================================================================


class MONKEY_OT_run_text_script(Operator):
    """テキストブロック内のスクリプトを実行"""
    bl_idname = "monkey.run_text_script"
    bl_label = "Run Text Script"
    bl_description = "選択したテキストブロックのスクリプトを実行"
    bl_options = {'REGISTER'}

    text_name: StringProperty(
        name="Text Name",
        description="実行するテキストブロック名",
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not self.text_name:
            self.report({'ERROR'}, "テキスト名が指定されていません")
            return {'CANCELLED'}

        text = bpy.data.texts.get(self.text_name)
        if not text:
            self.report({'ERROR'}, f"テキスト '{self.text_name}' が見つかりません")
            return {'CANCELLED'}

        try:
            # テキストエディタを開かずにスクリプトを実行
            # __main__ モジュールとして実行するため、適切な名前空間を設定
            log.debug(f"Executing script: {self.text_name}")
            script = text.as_string()
            namespace = {
                "__name__": "__main__",
                "__file__": text.name,
                "bpy": bpy,
            }
            exec(compile(script, text.name, 'exec'), namespace)
            log.info(f"Script executed successfully: {self.text_name}")
            self.report({'INFO'}, f"スクリプト '{self.text_name}' を実行しました")
        except Exception as e:
            log.error(f"Script execution failed: {self.text_name} - {str(e)}")
            self.report({'ERROR'}, f"実行エラー: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


# =============================================================================
# メニュー
# =============================================================================


class TOPBAR_MT_pluglug_run_scripts(Menu):
    """テキストスクリプト実行メニュー"""
    bl_idname = "TOPBAR_MT_pluglug_run_scripts"
    bl_label = "Run Scripts"

    def draw(self, context):
        layout = self.layout

        # .blendファイル内のテキストブロックを取得
        texts = [t for t in bpy.data.texts if not t.name.startswith(".")]

        if not texts:
            layout.label(text="テキストがありません", icon='INFO')
            return

        # テキストをリスト表示
        for text in sorted(texts, key=lambda t: t.name):
            # アイコンを決定（.py拡張子があればPythonアイコン）
            icon = 'FILE_SCRIPT' if text.name.endswith('.py') else 'TEXT'
            
            op = layout.operator(
                MONKEY_OT_run_text_script.bl_idname,
                text=text.name,
                icon=icon,
            )
            op.text_name = text.name


class TOPBAR_MT_pluglug(Menu):
    """Pluglug個人用メニュー"""
    bl_idname = "TOPBAR_MT_pluglug"
    bl_label = "Pluglug"

    def draw(self, context):
        layout = self.layout

        # スクリプト実行サブメニュー
        layout.menu(TOPBAR_MT_pluglug_run_scripts.bl_idname, icon='PLAY')

        # layout.separator()

        # 将来の拡張用プレースホルダー
        # ここに他の個人用機能を追加できます
        # layout.operator("...", text="...", icon='...')


# =============================================================================
# 登録
# =============================================================================


def draw_topbar_menu(self, context):
    """TOPBAR_MT_editor_menusにメニューを追加"""
    self.layout.menu(TOPBAR_MT_pluglug.bl_idname)


def register():
    bpy.types.TOPBAR_MT_editor_menus.append(draw_topbar_menu)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_topbar_menu)


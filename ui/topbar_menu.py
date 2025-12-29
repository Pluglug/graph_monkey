# pyright: reportInvalidTypeForm=false
"""
Topbar Menu Manager
トップバーに個人用メニューを追加するモジュール
"""

import bpy
from bpy.types import Menu

from ..operators.run_text_script import TOPBAR_MT_pluglug_run_scripts


class TOPBAR_MT_pluglug(Menu):
    """Pluglug個人用メニュー"""
    bl_idname = "TOPBAR_MT_pluglug"
    bl_label = "Pluglug"

    def draw(self, context):
        layout = self.layout

        # モーションルーレット
        layout.operator(
            "monkey.roulette_spin",
            text="Motion Roulette",
            icon='MOD_DYNAMICPAINT',
        )

        # オーバーレイ表示トグル / リセット
        result = context.window_manager.roulette_result
        if result.is_confirmed:
            icon = 'HIDE_OFF' if result.show_overlay else 'HIDE_ON'
            text = "テーマを非表示" if result.show_overlay else "テーマを表示"
            layout.operator(
                "monkey.roulette_toggle_overlay",
                text=text,
                icon=icon,
            )
            # layout.operator(
            #     "monkey.roulette_reset",
            #     text="リセット",
            #     icon='LOOP_BACK',
            # )

        layout.separator()

        # スクリプト実行サブメニュー
        layout.menu(TOPBAR_MT_pluglug_run_scripts.bl_idname, icon='PLAY')


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

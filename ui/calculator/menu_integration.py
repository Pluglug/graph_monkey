# pyright: reportInvalidTypeForm=false
"""
右クリックメニューへの電卓統合

数値プロパティの右クリックメニューに電卓オプションを追加します。
"""

import bpy
from ...utils.logging import get_logger
from ...utils.ui_utils import ic

log = get_logger(__name__)


def draw_calculator_entry(self, context):
    """数値プロパティの右クリックメニューに電卓エントリを描画"""
    # プロパティコンテキストをチェック
    ptr = getattr(context, "button_pointer", None)
    prop = getattr(context, "button_prop", None)

    if ptr and prop and prop.type in {"INT", "FLOAT"}:
        self.layout.separator()
        op = self.layout.operator(
            "wm.numeric_input", text="Calculator", icon=ic("TOPBAR")
        )
        log.debug("Calculator menu entry drawn")


def register_menu():
    """メニューエントリを登録"""
    try:
        bpy.types.UI_MT_button_context_menu.append(draw_calculator_entry)
        log.debug("Calculator menu integration registered")
    except Exception as e:
        log.error(f"Failed to register calculator menu: {e}")


def unregister_menu():
    """メニューエントリを登録解除"""
    try:
        bpy.types.UI_MT_button_context_menu.remove(draw_calculator_entry)
        log.debug("Calculator menu integration unregistered")
    except Exception as e:
        log.warning(f"Failed to unregister calculator menu: {e}")


# モジュールリロード対策
def cleanup_menu_on_reload():
    """モジュールリロード時のメニュークリーンアップ"""
    try:
        unregister_menu()
    except:
        pass  # エラーは無視（既に削除済みの場合）

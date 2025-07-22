"""
数値入力パネル（電卓）モジュール

このモジュールはBlenderの数値プロパティに対して、
電卓インターフェースを提供します。
"""

from .operators import (
    WM_OT_numeric_input,
    WM_OT_numeric_input_key,
)
from .preferences import CalculatorPreferences
from .menu_integration import register_menu, unregister_menu
from .core import cleanup_on_reload
from .menu_integration import cleanup_menu_on_reload

# モジュールリロード対策
cleanup_on_reload()
cleanup_menu_on_reload()


def register():
    """メニュー登録とキーマップ登録（クラス登録はaddon.pyが自動実行）"""
    register_menu()


def unregister():
    """メニュー登録解除のみ（クラス登録解除はaddon.pyが自動実行）"""
    unregister_menu()
